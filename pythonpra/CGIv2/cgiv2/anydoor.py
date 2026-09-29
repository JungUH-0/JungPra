"""AnyDoor 가중치 라인 래퍼.

이 모듈이 감싸는 구간은 **손대지 않는 부분**이다.

    DINOv2 -> projector -> ControlNet -> U-Net -> DDIM -> VAE

여기를 바꾸면 9.13GB 체크포인트가 무의미해진다. 특히 DINOv2 는 조건 경로가
하나뿐이라(텍스트 인코더가 없다) 교체하는 순간 projector·U-Net 크로스어텐션·
ControlNet 이 전부 죽고 VAE 84M 만 남는다.

그래서 이 파일은 **감싸기만** 한다. AnyDoor 저장소 파일은 수정하지 않는다.

원본 대비 달라진 점은 셋뿐이고, 셋 다 가중치와 무관하다.

  1. 체크포인트를 CPU 로 로드한다. 원본의 location='cuda' 는 9.8GB 를 GPU 에
     먼저 올려 10GB 카드에서 OOM 을 낸다.
  2. save_memory 일 때 최상위 버퍼를 직접 GPU 로 옮긴다. low_vram_shift 는
     서브모듈 넷만 옮기므로 betas/alphas_cumprod 가 CPU 에 남고, 그러면
     ddim_hacked.py 가 device 를 CPU 로 판단해 샘플링 전체가 CPU 에서 돈다.
  3. 참조 토큰을 캐싱한다. 원본은 합성마다 1.1B 모델을 돌린다. 객체 20 x
     배경 20 = 400 회 생성이면 400 번인데, 참조가 같으면 토큰도 같으므로
     20 번이면 된다.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import einops
import numpy as np
import torch


class AnyDoorEngine:
    """가중치 라인. 입력은 process_pairs 의 출력, 출력은 512 RGB."""

    def __init__(
        self,
        anydoor_root: str | Path,
        ckpt: str | Path | None = None,
        save_memory: bool = True,
        device: str = "cuda",
    ):
        self.root = Path(anydoor_root).resolve()
        if not (self.root / "cldm" / "cldm.py").exists():
            raise FileNotFoundError(f"AnyDoor 저장소가 아닙니다: {self.root}")

        # AnyDoor 는 상대 경로로 자기 설정을 읽으므로 sys.path 와 cwd 둘 다 필요하다.
        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))
        self._prev_cwd = Path.cwd()

        import os
        os.chdir(self.root)
        try:
            from cldm.model import create_model, load_state_dict
            from cldm.ddim_hacked import DDIMSampler
            from cldm.hack import disable_verbosity

            disable_verbosity()
            ckpt = Path(ckpt) if ckpt else self.root / "path" / "anydoor_pruned.ckpt"
            if not ckpt.exists():
                raise FileNotFoundError(f"체크포인트 없음: {ckpt}")

            self.model = create_model("./configs/anydoor.yaml").cpu()
            # location='cpu' 가 핵심. 'cuda' 면 체크포인트 전체가 먼저 VRAM 에 앉는다.
            self.model.load_state_dict(load_state_dict(str(ckpt), location="cpu"))

            self.save_memory = save_memory
            if save_memory:
                # low_vram_shift 가 안 옮기는 최상위 버퍼 (약 56KB)
                for k, v in list(self.model._buffers.items()):
                    if v is not None:
                        self.model._buffers[k] = v.to(device)
                self.model.low_vram_shift(is_diffusing=False)
            else:
                self.model = self.model.to(device)

            self.sampler = DDIMSampler(self.model)
        finally:
            os.chdir(self._prev_cwd)

        self.device = device
        self._token_cache: dict[str, torch.Tensor] = {}
        self._uncond: torch.Tensor | None = None

    # ── 조건 ────────────────────────────────────────────────────────────
    @staticmethod
    def _key(ref: np.ndarray) -> str:
        return hashlib.sha1(np.ascontiguousarray(ref).tobytes()).hexdigest()

    def encode_ref(self, ref: np.ndarray) -> torch.Tensor:
        """참조 224x224x3 (0~1 float) -> [1, 257, 1024]. 같은 참조는 재계산하지 않는다."""
        key = self._key(ref)
        hit = self._token_cache.get(key)
        if hit is not None:
            return hit

        x = torch.from_numpy(ref.copy()).float().to(self.device)
        x = einops.rearrange(x.unsqueeze(0), "b h w c -> b c h w").contiguous()
        with torch.no_grad():
            tok = self.model.get_learned_conditioning(x)
        self._token_cache[key] = tok
        return tok

    def _uncond_tokens(self) -> torch.Tensor:
        """무조건 조건. AnyDoor 는 빈 텍스트가 아니라 검은 224 이미지를 쓴다."""
        if self._uncond is None:
            with torch.no_grad():
                self._uncond = self.model.get_learned_conditioning(
                    [torch.zeros((1, 3, 224, 224), device=self.device)]
                )
        return self._uncond

    def cache_size(self) -> int:
        return len(self._token_cache)

    # ── 샘플링 ──────────────────────────────────────────────────────────
    def sample(
        self,
        item: dict,
        *,
        steps: int = 50,
        cfg: float = 5.0,
        control_strength: float = 1.0,
        seed: int | None = None,
        eta: float = 0.0,
        control_schedule=None,
    ) -> np.ndarray:
        """process_pairs 출력 -> 512x512x3 (0~255 float).

        control_schedule 를 주면 스텝마다 control_scales 를 갈아끼운다.
        시그니처는 f(step_index, total_steps) -> float 이다. 초반을 강하게 하고
        후반을 약하게 하면 형태를 먼저 잡고 조명을 나중에 융합하는 효과를 노릴
        수 있다 — 다만 검증된 바 없으므로 기본값은 상수다.
        """
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed % (2**32))

        hint = torch.from_numpy(item["hint"].copy()).float().to(self.device)
        hint = einops.rearrange(hint.unsqueeze(0), "b h w c -> b c h w").contiguous()

        cond_tok = self.encode_ref(item["ref"])
        cond = {"c_concat": [hint], "c_crossattn": [cond_tok]}
        uncond = {"c_concat": [hint], "c_crossattn": [self._uncond_tokens()]}

        self.model.control_scales = [control_strength] * 13
        callback = None
        if control_schedule is not None:
            def callback(i, _total=steps):
                s = float(control_schedule(i, _total))
                self.model.control_scales = [s] * 13

        if self.save_memory:
            self.model.low_vram_shift(is_diffusing=True)

        samples, _ = self.sampler.sample(
            steps, 1, (4, 64, 64), cond,
            verbose=False, eta=eta,
            unconditional_guidance_scale=cfg,
            unconditional_conditioning=uncond,
            callback=callback,
        )

        if self.save_memory:
            self.model.low_vram_shift(is_diffusing=False)

        with torch.no_grad():
            x = self.model.decode_first_stage(samples)
        x = einops.rearrange(x, "b c h w -> b h w c") * 127.5 + 127.5
        return np.clip(x[0].detach().cpu().numpy(), 0, 255)

    def peak_vram_gib(self) -> float:
        return torch.cuda.max_memory_allocated() / 2**30
