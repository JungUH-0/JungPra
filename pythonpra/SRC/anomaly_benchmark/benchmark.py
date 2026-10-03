"""
2단계: PaDiM / PatchCore / EfficientAD 벤치마크 (정확도 + 추론 속도) 와 그래프

한 번의 실행(= 모델 1개 x 장수 1개 x 시드 1개)마다
    fit -> test(AUROC, F1) -> 점수 저장 -> 추론 속도 측정 -> 체크포인트 사본 -> CSV 한 행 추가
를 수행한다. 한 행씩 바로 기록하므로 중간에 죽어도 앞선 결과가 남는다.

실행 예시
    python benchmark.py                                     # 100/200/300장 x 3모델 전체
    python benchmark.py --smoke                             # 동작 확인용 (원본 전체 x 3모델, EfficientAD 100 step)
    python benchmark.py --counts 100 --models padim         # 일부만
    python benchmark.py --seeds 42 43 44                    # 시드 반복
    python benchmark.py --plot-only                         # 학습 없이 저장된 CSV 로 그래프만

추론 속도 측정 규칙 (명세 6장)
    배치 1, 워밍업 후 측정, 측정 전후 cuda.synchronize, 이미지 로딩·GPU 전송 제외.
    model(x) 는 전처리(리사이즈·정규화) + 모델 + 후처리를 포함한다.
"""

import argparse
import csv
import gc
import shutil
import time
from pathlib import Path

import numpy as np

import common
from common import (
    ANOMALIB_OUT_DIR, CKPT_DIR, DATASET_DIR, EFFICIENTAD_STEPS, MODEL_NAMES, PLOTS_DIR,
    RESULTS_DIR, SCORES_DIR, SEED, TRAIN_COUNTS, build_datamodule, build_engine, build_model,
    category_name, model_notes, run_tag,
)

CSV_COLUMNS = [
    "train_count", "model", "image_auroc", "pixel_auroc", "image_f1", "latency_ms", "fps",
    "gpu_mem_mb", "fit_time_s", "seed", "ckpt_path", "notes",
]
MODEL_LABEL = {"padim": "PaDiM", "patchcore": "PatchCore", "efficientad": "EfficientAD"}
MODEL_COLOR = {"padim": "#1f77b4", "patchcore": "#d62728", "efficientad": "#2ca02c"}


# ----------------------------------------------------------------------
# 출력 위치 (smoke 는 본 결과와 섞이지 않게 results/smoke 아래로 분리)
# ----------------------------------------------------------------------
class Paths:
    def __init__(self, smoke: bool):
        root = RESULTS_DIR / "smoke" if smoke else RESULTS_DIR
        self.csv = root / "benchmark_results.csv"
        self.scores = root / "scores"
        self.plots = root / "plots"
        self.anomalib_out = root / "anomalib"
        self.ckpt = root / "checkpoints" if smoke else CKPT_DIR


# ----------------------------------------------------------------------
# 한 번의 실행
# ----------------------------------------------------------------------
def collect_scores(engine, model, datamodule, out_csv: Path) -> np.ndarray:
    """test 셋 이미지별 (파일명, 점수, 정답 라벨)을 저장하고 (점수, 라벨) 배열을 돌려준다."""
    predictions = engine.predict(model=model, datamodule=datamodule)
    rows = []
    for batch in predictions:
        paths = common._as_list(batch.image_path)
        scores = common._as_list(batch.pred_score)
        labels = common._as_list(batch.gt_label)
        for p, s, l in zip(paths, scores, labels):
            rows.append((Path(p).parent.name + "/" + Path(p).name,
                         float(np.asarray(s).item()), int(np.asarray(l).item())))
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "score", "label"])
        w.writerows(rows)
    return np.array([[r[1], r[2]] for r in rows])


def measure_latency(model, count, warmup: int = 10, n_iter: int = 100):
    """배치 1 추론 시간(ms/장), FPS, GPU 최대 메모리(MB)를 잰다."""
    import torch
    from PIL import Image

    device = "cuda" if torch.cuda.is_available() else "cpu"
    sync = torch.cuda.synchronize if device == "cuda" else (lambda: None)
    model = model.to(device).eval()

    test_files = sorted((DATASET_DIR / category_name(count) / "test").rglob("*.png"))
    step = max(1, len(test_files) // 20)           # test 전체에서 고르게 20장
    tensors = []
    for p in test_files[::step][:20]:
        arr = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0
        tensors.append(torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device))

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        for i in range(warmup):                     # 첫 실행은 CUDA 초기화로 느리다
            model(tensors[i % len(tensors)])
        sync()
        t0 = time.perf_counter()
        for i in range(n_iter):
            model(tensors[i % len(tensors)])
        sync()
        elapsed = time.perf_counter() - t0
    ms = elapsed / n_iter * 1000
    mem = torch.cuda.max_memory_allocated() / 1024**2 if device == "cuda" else float("nan")
    return ms, 1000.0 / ms, mem


def run_one(model_name, count, seed, args, paths: Paths) -> dict:
    from lightning.pytorch import seed_everything
    from sklearn.metrics import roc_auc_score

    seed_everything(seed, workers=True)
    tag = run_tag(model_name, count, seed)
    print(f"\n{'=' * 70}\n실행: {tag}  (학습 이미지 {'전체' if count is None else count}장)\n{'=' * 70}")

    train_bs = 1 if model_name == "efficientad" else args.batch_size   # EfficientAD 는 배치 1 필수
    datamodule = build_datamodule(count, train_bs, args.batch_size, args.num_workers)
    model = build_model(model_name)
    engine = build_engine(model_name, args.effad_steps, default_root_dir=paths.anomalib_out)

    t0 = time.perf_counter()
    engine.fit(model=model, datamodule=datamodule)
    fit_time = time.perf_counter() - t0

    results = engine.test(model=model, datamodule=datamodule)[0]
    image_auroc = float(results.get("image_AUROC", float("nan")))
    pixel_auroc = float(results.get("pixel_AUROC", float("nan")))
    image_f1 = float(results.get("image_F1Score", float("nan")))

    # 점수·라벨 저장 + 직접 계산한 AUROC 가 anomalib 출력과 일치하는지 확인
    arr = collect_scores(engine, model, datamodule, paths.scores / f"{tag}.csv")
    my_auroc = float(roc_auc_score(arr[:, 1], arr[:, 0]))
    diff = abs(my_auroc - image_auroc)
    print(f"[검증] image AUROC  anomalib={image_auroc:.4f}  sklearn={my_auroc:.4f}  차이={diff:.2e}"
          f"  {'OK' if diff < 1e-3 else '불일치 - 점수/라벨 추출 확인 필요'}")

    ms, fps, mem = measure_latency(model, count)
    print(f"[속도] {ms:.2f} ms/장  {fps:.1f} FPS  GPU 최대 {mem:.0f} MB")

    src = engine.best_model_path
    if not src or not Path(src).exists():
        raise FileNotFoundError(f"체크포인트를 찾지 못했다: {src!r}")
    dst = paths.ckpt / f"{tag}.ckpt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    row = dict(
        train_count=len(list((DATASET_DIR / category_name(count) / "train" / "good").glob("*.png"))),
        model=model_name, image_auroc=round(image_auroc, 4), pixel_auroc=round(pixel_auroc, 4),
        image_f1=round(image_f1, 4), latency_ms=round(ms, 3), fps=round(fps, 2),
        gpu_mem_mb=round(mem, 1), fit_time_s=round(fit_time, 1), seed=seed, ckpt_path=str(dst),
        notes=model_notes(model_name, args.effad_steps) + f";auroc_diff={diff:.1e}",
    )
    # 다음 실행에 메모리가 쌓이지 않게 정리
    del model, engine, datamodule
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    return row


def append_row(csv_path: Path, row: dict) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    new = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if new:
            w.writeheader()
        w.writerow(row)


def done_keys(csv_path: Path) -> set:
    """이미 끝난 (ckpt 파일명) 집합. 재실행 시 건너뛰는 데 쓴다."""
    if not csv_path.exists():
        return set()
    import pandas as pd
    return {Path(p).stem for p in pd.read_csv(csv_path)["ckpt_path"]}


# ----------------------------------------------------------------------
# 그래프 (저장된 CSV 만 사용, 학습과 분리)
# ----------------------------------------------------------------------
def plot_all(paths: Paths) -> None:
    import matplotlib

    matplotlib.use("Agg")   # VS Code 디버거의 Qt 연동 오류 회피
    import matplotlib.pyplot as plt
    import pandas as pd
    from sklearn.metrics import roc_auc_score, roc_curve

    if not paths.csv.exists():
        print(f"결과 CSV 가 없다: {paths.csv}")
        return
    df = pd.read_csv(paths.csv)
    paths.plots.mkdir(parents=True, exist_ok=True)
    counts = sorted(df["train_count"].unique())
    models = [m for m in MODEL_NAMES if m in set(df["model"])]

    def roc_of(row):
        f = paths.scores / (Path(row["ckpt_path"]).stem + ".csv")
        if not f.exists():
            return None
        s = pd.read_csv(f)
        fpr, tpr, _ = roc_curve(s["label"], s["score"])
        return fpr, tpr, roc_auc_score(s["label"], s["score"])

    base = df[df["seed"] == SEED] if (df["seed"] == SEED).any() else df   # ROC 는 기본 시드로

    def roc_figure(sel_rows, key, title, fname, label_fn, color_fn):
        fig, ax = plt.subplots(figsize=(5.5, 5))
        for _, r in sel_rows.iterrows():
            roc = roc_of(r)
            if roc is None:
                continue
            ax.plot(roc[0], roc[1], color=color_fn(r), label=f"{label_fn(r)} (AUROC {roc[2]:.3f})")
        ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="random")
        ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title=title)
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        fig.savefig(paths.plots / fname, dpi=130)
        plt.close(fig)

    # 1) 장수별 ROC (모델 3개 겹침)
    for c in counts:
        roc_figure(base[base["train_count"] == c], "model", f"ROC - train {c} images",
                   f"roc_count_{c}.png", lambda r: MODEL_LABEL[r["model"]], lambda r: MODEL_COLOR[r["model"]])
    # 2) 모델별 ROC (장수 겹침)
    cmap = plt.get_cmap("viridis")
    for m in models:
        sub = base[base["model"] == m].sort_values("train_count")
        idx = {c: i for i, c in enumerate(sorted(sub["train_count"]))}
        roc_figure(sub, "train_count", f"ROC - {MODEL_LABEL[m]}", f"roc_model_{m}.png",
                   lambda r: f"{int(r['train_count'])} images",
                   lambda r: cmap(idx[r["train_count"]] / max(1, len(idx) - 1) * 0.85))

    # 평균·편차 (시드 반복 시 오차 막대)
    agg = df.groupby(["model", "train_count"]).agg(
        image_mean=("image_auroc", "mean"), image_std=("image_auroc", "std"),
        pixel_mean=("pixel_auroc", "mean"), pixel_std=("pixel_auroc", "std"),
        lat=("latency_ms", "mean"),
    ).fillna(0).reset_index()

    # 3) AUROC 막대그래프 (모델 x 장수 묶음, Image / Pixel)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    width = 0.8 / len(counts)
    for ax, kind in zip(axes, ("image", "pixel")):
        for j, c in enumerate(counts):
            vals, errs = [], []
            for m in models:
                r = agg[(agg["model"] == m) & (agg["train_count"] == c)]
                vals.append(r[f"{kind}_mean"].iloc[0] if len(r) else np.nan)
                errs.append(r[f"{kind}_std"].iloc[0] if len(r) else 0)
            xs = np.arange(len(models)) + j * width - 0.4 + width / 2
            bars = ax.bar(xs, vals, width, yerr=errs, capsize=3, label=f"{int(c)} images")
            ax.bar_label(bars, fmt="%.3f", fontsize=7, padding=2)
        ax.set_xticks(range(len(models)), [MODEL_LABEL[m] for m in models])
        ax.set(ylabel=f"{kind.capitalize()} AUROC", title=f"{kind.capitalize()} AUROC", ylim=(0.5, 1.05))
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(paths.plots / "auroc_bar.png", dpi=130)
    plt.close(fig)

    # 4) 장수 민감도 선 그래프
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, kind in zip(axes, ("image", "pixel")):
        for m in models:
            sub = agg[agg["model"] == m].sort_values("train_count")
            ax.errorbar(sub["train_count"], sub[f"{kind}_mean"], yerr=sub[f"{kind}_std"], marker="o",
                        capsize=3, color=MODEL_COLOR[m], label=MODEL_LABEL[m])
        ax.set(xlabel="Train images", ylabel=f"{kind.capitalize()} AUROC",
               title=f"{kind.capitalize()} AUROC vs train size", xticks=counts)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(paths.plots / "auroc_vs_count.png", dpi=130)
    plt.close(fig)

    # 5) 정확도·속도 산점도
    fig, ax = plt.subplots(figsize=(6.5, 5))
    markers = dict(zip(counts, ["o", "s", "^", "D", "v"]))
    for _, r in agg.iterrows():
        ax.scatter(r["lat"], r["image_mean"], color=MODEL_COLOR[r["model"]],
                   marker=markers[r["train_count"]], s=70)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ls="", label=MODEL_LABEL[m]) for m in models]
    handles += [Line2D([], [], color="gray", marker=markers[c], ls="", label=f"{int(c)} images") for c in counts]
    ax.legend(handles=handles, fontsize=8)
    ax.set(xlabel="Inference time (ms / image)", ylabel="Image AUROC", title="Accuracy vs speed")
    fig.tight_layout()
    fig.savefig(paths.plots / "accuracy_vs_speed.png", dpi=130)
    plt.close(fig)
    print(f"그래프 저장 위치: {paths.plots}")


# ----------------------------------------------------------------------
# 진입점
# ----------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="PaDiM / PatchCore / EfficientAD 벤치마크",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--counts", nargs="+", default=[str(c) for c in TRAIN_COUNTS],
                   help="학습 장수. 'full' 은 원본 hazelnut 전체")
    p.add_argument("--models", nargs="+", default=list(MODEL_NAMES), choices=MODEL_NAMES)
    p.add_argument("--seeds", nargs="+", type=int, default=[SEED])
    p.add_argument("--effad-steps", type=int, default=EFFICIENTAD_STEPS, help="EfficientAD 학습 step 수")
    p.add_argument("--batch-size", type=int, default=8, help="PaDiM/PatchCore 학습 배치, 평가 배치")
    p.add_argument("--num-workers", type=int, default=4)
    p.add_argument("--smoke", action="store_true",
                   help="동작 확인: 원본 전체 x 모델, EfficientAD 100 step, 출력은 results/smoke 로 분리")
    p.add_argument("--rerun", action="store_true", help="CSV 에 이미 있는 실행도 다시 한다")
    p.add_argument("--plot-only", action="store_true", help="학습 없이 CSV 로 그래프만 그린다")
    args = p.parse_args()

    if args.smoke:
        args.counts = ["full"]
        if args.effad_steps == EFFICIENTAD_STEPS:
            args.effad_steps = 100
    paths = Paths(args.smoke)

    if args.plot_only:
        plot_all(paths)
        return

    counts = [None if c == "full" else int(c) for c in args.counts]
    done = set() if args.rerun else done_keys(paths.csv)
    for seed in args.seeds:
        for count in counts:
            for model_name in args.models:
                if run_tag(model_name, count, seed) in done:
                    print(f"건너뜀(이미 완료): {run_tag(model_name, count, seed)}")
                    continue
                row = run_one(model_name, count, seed, args, paths)
                append_row(paths.csv, row)
                print(f"[기록] {paths.csv}")
    plot_all(paths)


if __name__ == "__main__":
    main()
