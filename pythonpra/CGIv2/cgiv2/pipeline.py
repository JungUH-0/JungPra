"""전처리 -> 가중치 라인 -> 후처리 연결.

가중치 라인(AnyDoorEngine)은 손대지 않는다. 이 파일이 하는 일은 그 앞뒤를
맞춰 끼우는 것뿐이다.

    mask.py   마스크 생성        AnyDoor 에 없음
    prep.py   객체별 정규화      AnyDoor 에 없음
    pairs.py  규약 맞추기        AnyDoor 규약을 지킴 (세 벌 통합)
    ─────────────────────────────────────────────
    anydoor.py                   손대지 않음
    ─────────────────────────────────────────────
    pairs.crop_back              역변환 + 페더링
    paste.py                     되붙일 범위 (크롭 / 박스 / 인물)
    postproc.py                  AnyDoor 에 없음
    shadow.py                    접지 · 투영 그림자
    evaluate.py                  AnyDoor 에 없음
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import paste, postproc, prep, shadow
from .face_restore import FaceTransplanter
from .pairs import PairBuilder, crop_back


@dataclass
class Settings:
    """전부 한 곳에. 격자 탐색은 이 필드를 바꿔가며 돈다."""

    # 가중치 라인 (추론 파라미터 — 가중치와 무관)
    steps: int = 50
    cfg: float = 5.0
    control_strength: float = 1.0
    seed: int | None = 1234

    # 전처리
    shape_control: bool = False      # 강체는 True 를 시험해볼 것
    tar_crop_ratio: float = 2.0      # 추론 고정값 (원본은 1.5~3.0 랜덤)
    normalize_object: bool = True    # 면적비를 관문 안으로

    # 후처리 — 기본 전부 꺼짐. 베이스라인 측정 후에만 켠다.
    feather: int = 0
    color_match: float = 0.0
    color_tool: str = "lab"          # lab | hist
    shadow: bool = False

    # 도구 선택 (가중치와 무관한 🟢 등급)
    mask_tool: str = "birefnet_hr"   # 기록용. 마스크는 밖에서 만들어 넣는다
    blend_tool: str = "feather"      # feather | poisson | poisson_mixed | none

    # 얼굴 정체성 복원 (2026-09-22) — 기본 꺼짐. 원본 얼굴을 정렬해 이식한다.
    # AnyDoor 는 object-level 모델이라 얼굴 정체성을 안 지킨다(실측 0.107,
    # 판정선 0.363). 상반신 크롭만으로는 부족했다(0.131). 이식하면 0.95.
    face_restore: bool = False
    face_head_room: float = 0.6
    face_torso_ratio: float = 1.3
    face_width_ratio: float = 1.7
    face_feather: float = 0.10
    face_color_match: float = 0.5
    face_blend: str = "feather"      # feather | poisson

    # 되붙이기 (2026-09-23) — 기본 crop = 원본과 같이 크롭 전체. paste.py 참조.
    # crop 은 크롭(화면의 41~67%) 안 배경을 원본 선명도의 9~30% 인 재생성본으로
    # 바꾼다. person 은 분할 도구가 필요하다 — 없거나 실패하면 box 로 물러난다.
    paste: str = "crop"              # crop | box | person | object(= person, 2안용 이름)
    paste_margin: float = 0.08
    paste_min_aspect: float = 0.6
    paste_thresh: float = 0.5
    paste_min_inside: float = 0.5
    paste_grow: float = 0.01
    paste_fg: str = "blur_fusion"    # blur_fusion | none — 경계의 생성 배경색 제거

    # 그림자 도구 (2026-09-26) — shadow=True 일 때만. shadow.py 참조.
    # offset 은 기존 postproc.add_contact_shadow (실루엣 평행이동).
    shadow_tool: str = "contact"     # contact | cast | offset
    contact_strength: float = 0.5
    contact_width: float = 1.25      # 넓은 타원 가로 = 발 폭/2 × 이 값
    contact_height: float = 0.03     # 넓은 타원 세로 = 키 × 이 값 (자동차는 더 두껍게)
    cast_strength: float = 0.45      # sun["beta"] 가 없을 때만 쓰는 회색 진하기
    sun: dict | None = None          # shadow.estimate_sun 결과. cast 에 필요

    def tag(self) -> str:
        """결과 파일명에 붙일 설정 요약."""
        t = f"cfg{self.cfg:g}_s{self.control_strength:g}_st{self.steps}"
        if self.shape_control:
            t += "_shape"
        if self.mask_tool != "birefnet_hr":
            t += f"_{self.mask_tool}"
        if self.blend_tool != "feather" or self.feather:
            t += f"_{self.blend_tool}{self.feather or ''}"
        if self.color_match:
            t += f"_{self.color_tool}{self.color_match:g}"
        if self.shadow:
            t += "_sh" if self.shadow_tool == "offset" else f"_sh-{self.shadow_tool}"
        if self.paste != "crop":
            t += f"_paste-{self.paste}"
            if self.paste in {"person", "object"} and self.paste_fg != "blur_fusion":
                t += f"-{self.paste_fg}"
        if self.face_restore:
            t += "_facerestore"
        return t


@dataclass
class Result:
    image: np.ndarray
    region: np.ndarray               # 원본 좌표계의 배치 영역
    skipped: str | None = None       # 관문 탈락 사유
    notes: list[str] = field(default_factory=list)

    # 후처리 도구를 GPU 없이 갈아끼우기 위한 중간 산출물.
    # 확산은 한 번만 돌리고, 블렌딩·색 정합은 이걸로 몇 번이든 다시 한다.
    raw: np.ndarray | None = None            # 512x512x3 모델 출력
    extra_sizes: np.ndarray | None = None    # crop_back 용 H1,W1,H2,W2
    crop_box: np.ndarray | None = None       # crop_back 용 y1,y2,x1,x2

    def repost(self, background: np.ndarray, st: "Settings",
              ref_image: np.ndarray | None = None,
              ref_mask: np.ndarray | None = None,
              transplanter: FaceTransplanter | None = None,
              masker=None) -> np.ndarray:
        """저장된 raw 로 후처리만 다시 적용한다. 확산 모델을 안 쓴다.

        st.face_restore 를 쓰려면 ref_image/ref_mask/transplanter 를 넘겨야
        한다 — 얼굴 이식은 참조 원본이 필요해서 raw 만으로는 재현할 수 없다.
        st.paste="person" 은 masker(분할 도구)가 필요하다. 사유는 self.notes 에 남는다.
        """
        if self.raw is None:
            raise RuntimeError("raw 가 없습니다 (keep_raw=False 로 생성됨)")
        return _finish(self.raw, background, self.region,
                       self.extra_sizes, self.crop_box, st,
                       ref_image, ref_mask, transplanter,
                       masker=masker, notes=self.notes)


def _finish(raw, background, region, extra_sizes, crop_box, st: "Settings",
           ref_image=None, ref_mask=None, transplanter: FaceTransplanter | None = None,
           masker=None, notes: list[str] | None = None):
    """512 예측 -> 원본 좌표 복원 -> 블렌딩 -> 얼굴 복원 -> 되붙이기 -> 색 정합/그림자.

    도구 선택이 전부 여기 모여 있다. 전부 🟢 등급이라 가중치와 무관하다.

    얼굴 복원이 되붙이기보다 **먼저**다 (2026-09-23 순서 변경). 이식은 참조
    실루엣을 가우시안으로 흐려 섞으므로 가장자리가 실루엣 밖(참조 사진의 크림색
    스튜디오 배경)까지 번진다. 생성 배경 위에서는 안 보이던 이 테두리가, 되붙이기
    뒤에 원본의 어두운 배경 위에서 이식하면 머리 둘레 흰 테두리로 드러났다(W09).
    먼저 이식하면 테두리는 생성 배경 쪽에 떨어지고 되붙이기가 그 배경을 버린다.
    """
    hard = crop_back(raw, background, extra_sizes, crop_box, feather=0)

    if st.blend_tool == "feather":
        out = crop_back(raw, background, extra_sizes, crop_box, feather=st.feather)
    elif st.blend_tool in {"poisson", "poisson_mixed"}:
        out = postproc.blend_poisson(hard, background, region,
                                     mixed=st.blend_tool.endswith("mixed"))
    else:                                   # none — 원본과 같은 하드 대입
        out = hard

    if st.face_restore and transplanter is not None and ref_image is not None and ref_mask is not None:
        # 실패(얼굴 미검출 등)해도 조용히 out 을 그대로 쓴다 — 이식은 보강이지
        # 필수 단계가 아니다. 성공 여부가 필요하면 transplanter.transplant() 를
        # 직접 불러 두 번째 반환값을 본다.
        restored, _ok = transplanter.transplant(
            ref_image, ref_mask, out,
            head_room=st.face_head_room, torso_ratio=st.face_torso_ratio,
            width_ratio=st.face_width_ratio, feather=st.face_feather,
            color_match=st.face_color_match, blend=st.face_blend)
        out = restored

    # 되붙이기 — 크롭 중 어디까지 남길지. 이후 단계의 기준 영역도 여기서 정한다:
    # person 이면 배치 박스 대신 인물 실루엣. 박스에는 이제 원본 배경이 섞여 있어
    # 박스 기준으로 색을 맞추면 원본 픽셀까지 바뀐다.
    if st.paste not in {"crop", "box", "person", "object"}:
        raise ValueError(f"모르는 되붙이기 방식: {st.paste}")
    # object 는 person 과 같은 동작의 2안용 이름 — 분할은 사람·물건을 가리지 않는다
    mode, post_region = ("person" if st.paste == "object" else st.paste), region
    if mode == "person":
        if masker is None:
            alpha, info = None, {"why": "분할 도구 없음"}
        else:
            alpha, info = paste.person_alpha(
                out, region, crop_box, masker,
                margin=st.paste_margin, min_aspect=st.paste_min_aspect,
                thresh=st.paste_thresh, min_inside=st.paste_min_inside,
                grow=st.paste_grow)
        if alpha is None:
            mode = "box"                    # 원저자 데모 방식으로 물러난다
            if notes is not None:
                notes.append(f"되붙이기 person 실패({info['why']}) → box")
        else:
            fg = paste.estimate_foreground(out, alpha) if st.paste_fg == "blur_fusion" else None
            out = paste.compose(out, background, alpha, fg=fg)
            post_region = (alpha > st.paste_thresh).astype(np.uint8)
            if info["touches_window"] and notes is not None:
                notes.append("되붙이기: 분할 대상이 창 가장자리에 닿음 — 잘렸을 수 있다")
    if mode == "box":
        alpha = paste.box_alpha(region, crop_box, feather=st.feather)
        if alpha is not None:
            out = paste.compose(out, background, alpha)

    if st.shadow_tool not in {"contact", "cast", "offset"}:
        raise ValueError(f"모르는 그림자 도구: {st.shadow_tool}")
    out = postproc.apply(out, post_region,
                         color_match=st.color_match, color_tool=st.color_tool,
                         shadow=st.shadow and st.shadow_tool == "offset", shadow_opacity=0.35)
    if st.shadow and st.shadow_tool in {"contact", "cast"}:
        # person 이면 post_region 이 인물 실루엣이라 발 선이 정확하다.
        # crop/box 면 배치 박스 아랫변을 발로 본다 (근사).
        out = shadow.apply(out, post_region, st.shadow_tool,
                           contact_strength=st.contact_strength,
                           contact_width=st.contact_width, contact_height=st.contact_height,
                           sun=st.sun, cast_strength=st.cast_strength, notes=notes)
    return out


class Compositor:
    def __init__(self, engine, anydoor_root: str | Path,
                face_transplanter: FaceTransplanter | None = None,
                paste_masker=None):
        """face_transplanter 를 주면 Settings.face_restore=True 일 때 얼굴을
        복원한다. 안 주면 face_restore 가 켜져 있어도 조용히 건너뛴다 —
        검출기(YuNet/SFace) 로딩 비용이 있어서 기본으로 만들지 않는다.

        paste_masker 는 Settings.paste="person" 용 분할 도구 (mask.get_masker).
        안 주면 box 로 물러나고 Result.notes 에 남긴다. AnyDoor venv 에서는
        BiRefNet 이 안 돌 수 있어 raw 를 남긴 뒤 CGI venv 에서 repost 한다.
        """
        self.engine = engine
        self.builder = PairBuilder(anydoor_root)
        self.face_transplanter = face_transplanter
        self.paste_masker = paste_masker

    def __call__(
        self,
        ref_image: np.ndarray,
        ref_mask: np.ndarray,
        bg_image: np.ndarray,
        bg_mask: np.ndarray,
        st: Settings | None = None,
        *,
        keep_raw: bool = False,
    ) -> Result:
        st = st or Settings()
        notes: list[str] = []

        # ── 전처리 ──────────────────────────────────────────────────
        if st.normalize_object:
            ref_image, ref_mask, why = prep.normalize_object(ref_image, ref_mask)
            notes.append(f"참조 {why}")

        bad = self.builder.check_gates(ref_mask, bg_mask)
        if bad:
            # 여기서 멈추지 않으면 학습 경로에서는 무한 재시도로 조용히 멈추고,
            # 추론 경로에서는 assert 가 없어 이상한 결과만 나온다.
            return Result(bg_image, bg_mask, skipped=" / ".join(bad), notes=notes)

        item = self.builder.build(
            ref_image, ref_mask, bg_image, bg_mask,
            train=False,
            shape_control=st.shape_control,
            tar_crop_ratio=st.tar_crop_ratio,
        )

        # ── 가중치 라인 (손대지 않음) ────────────────────────────────
        pred = self.engine.sample(
            item,
            steps=st.steps,
            cfg=st.cfg,
            control_strength=st.control_strength,
            seed=st.seed,
        )

        # ── 후처리 ──────────────────────────────────────────────────
        out = _finish(pred, bg_image, bg_mask,
                      item["extra_sizes"], item["tar_box_yyxx_crop"], st,
                      ref_image, ref_mask, self.face_transplanter,
                      masker=self.paste_masker, notes=notes)
        return Result(
            out, bg_mask, notes=notes,
            raw=pred if keep_raw else None,
            extra_sizes=item["extra_sizes"] if keep_raw else None,
            crop_box=item["tar_box_yyxx_crop"] if keep_raw else None,
        )


def load_pair(obj_path, obj_mask_path, bg_path):
    """파일에서 (참조 RGB, 참조 마스크, 배경 RGB) 를 읽는다."""
    import cv2
    from .mask import load_mask

    ref = cv2.cvtColor(cv2.imread(str(obj_path)), cv2.COLOR_BGR2RGB)
    rm = load_mask(obj_mask_path)
    bg = cv2.cvtColor(cv2.imread(str(bg_path)), cv2.COLOR_BGR2RGB)
    if rm.shape != ref.shape[:2]:
        rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]),
                        interpolation=cv2.INTER_NEAREST)
    return ref, rm, bg
