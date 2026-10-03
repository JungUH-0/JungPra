"""
1단계: hazelnut 원본 준비와 학습 장수별(100/200/300) 분할

동작
    1) 원본을 dataset/hazelnut 으로 복사한다. (이미 있으면 건너뜀, 원본은 건드리지 않음)
       --source 는 압축 해제된 폴더 또는 hazelnut.tar.xz 모두 가능하다.
    2) train/good 파일명을 정렬 -> 시드 고정 셔플 -> 앞 300/200/100장 선택
       (한 번만 섞으므로 100 ⊂ 200 ⊂ 300 이 자동 보장된다)
    3) dataset/hazelnut_N/ 에 선택한 train/good 을 복사하고, test, ground_truth 는 원본 그대로 복사한다.
    4) 선택된 파일명은 dataset/splits/hazelnut_N.txt 에 저장한다.

실행 예시
    python split_dataset.py
    python split_dataset.py --source D:/data/hazelnut.tar.xz
    python split_dataset.py --overwrite          # 이미 있는 hazelnut_N 을 지우고 다시 만든다
"""

import argparse
import random
import shutil
import tarfile
from pathlib import Path

from common import CATEGORY, DATASET_DIR, SEED, TRAIN_COUNTS

DEFAULT_SOURCE = Path.home() / "Downloads" / CATEGORY
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp"}


def _images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)


def report_counts(root: Path) -> None:
    """train/good, test, ground_truth 하위 폴더별 이미지 수를 출력한다."""
    for part in ("train", "test", "ground_truth"):
        base = root / part
        if not base.is_dir():
            print(f"  [누락] {base}")
            continue
        subs = sorted(d for d in base.iterdir() if d.is_dir())
        text = ", ".join(f"{d.name} {len(_images(d))}" for d in subs)
        print(f"  {part:<13} {text}")


def prepare_original(source: Path, overwrite: bool) -> Path:
    """원본을 dataset/hazelnut 으로 복사(또는 압축 해제)한다."""
    dest = DATASET_DIR / CATEGORY
    if dest.is_dir() and not overwrite:
        print(f"[원본] {dest} 이미 있음 -> 건너뜀")
        return dest
    if not source.exists():
        raise FileNotFoundError(f"원본이 없다: {source}\n--source 로 위치를 지정한다.")
    if dest.is_dir():
        shutil.rmtree(dest)

    if source.is_file() and "".join(source.suffixes) in (".tar.xz", ".tar"):
        print(f"[원본] 압축 해제: {source} -> {DATASET_DIR}")
        with tarfile.open(source) as tar:
            tar.extractall(DATASET_DIR)   # 압축 안의 최상위 폴더가 hazelnut
    else:
        print(f"[원본] 복사: {source} -> {dest}")
        shutil.copytree(source, dest)

    if not (dest / "train" / "good").is_dir():
        raise RuntimeError(f"복사 후 구조가 맞지 않다: {dest}/train/good 없음")
    return dest


def make_splits(orig: Path, counts, seed: int, overwrite: bool) -> None:
    good = [p.name for p in _images(orig / "train" / "good")]   # 정렬된 목록
    if len(good) < max(counts):
        raise RuntimeError(f"학습 이미지가 부족하다: {len(good)}장 < {max(counts)}장")

    shuffled = good[:]
    random.Random(seed).shuffle(shuffled)   # 한 번만 섞는다
    print(f"\n[분할] 원본 train/good {len(good)}장, seed={seed}")

    split_dir = DATASET_DIR / "splits"
    split_dir.mkdir(exist_ok=True)

    for n in sorted(counts):
        out = DATASET_DIR / f"{CATEGORY}_{n}"
        if out.is_dir():
            if not overwrite:
                print(f"  hazelnut_{n}: 이미 있음 -> 건너뜀 (--overwrite 로 재생성)")
                continue
            shutil.rmtree(out)

        chosen = sorted(shuffled[:n])
        (out / "train" / "good").mkdir(parents=True)
        for name in chosen:
            shutil.copy2(orig / "train" / "good" / name, out / "train" / "good" / name)
        shutil.copytree(orig / "test", out / "test")
        shutil.copytree(orig / "ground_truth", out / "ground_truth")
        (split_dir / f"{CATEGORY}_{n}.txt").write_text("\n".join(chosen) + "\n", encoding="utf-8")
        print(f"  hazelnut_{n}: train/good {len(chosen)}장 복사, test·ground_truth 원본 복사")


def verify(counts) -> None:
    """포함 관계와 test 동일성을 확인하고 폴더별 장수를 출력한다."""
    split_dir = DATASET_DIR / "splits"
    sets = {n: set((split_dir / f"{CATEGORY}_{n}.txt").read_text(encoding="utf-8").split())
            for n in sorted(counts) if (split_dir / f"{CATEGORY}_{n}.txt").exists()}
    ns = sorted(sets)
    for a, b in zip(ns, ns[1:]):
        print(f"  {a} ⊂ {b}: {sets[a] <= sets[b]}")

    print("\n[확인] 폴더별 이미지 수")
    for name in [CATEGORY] + [f"{CATEGORY}_{n}" for n in sorted(counts)]:
        root = DATASET_DIR / name
        if root.is_dir():
            print(f"{name}")
            report_counts(root)


def main() -> None:
    p = argparse.ArgumentParser(description="hazelnut 원본 준비 및 100/200/300장 분할",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="원본 폴더 또는 .tar.xz")
    p.add_argument("--seed", type=int, default=SEED, help="셔플 시드")
    p.add_argument("--counts", type=int, nargs="+", default=list(TRAIN_COUNTS), help="학습 장수")
    p.add_argument("--overwrite", action="store_true", help="이미 있는 출력 폴더를 지우고 다시 만든다")
    args = p.parse_args()

    orig = DATASET_DIR / CATEGORY
    if not orig.is_dir() and not args.source.exists():
        print(f"원본 hazelnut 이 없다: {orig}\n--source 로 원본 폴더 또는 hazelnut.tar.xz 를 지정한다.")
        return
    orig = prepare_original(args.source, overwrite=False)   # 원본 폴더 재복사는 수동으로만
    make_splits(orig, args.counts, args.seed, args.overwrite)
    verify(args.counts)


if __name__ == "__main__":
    main()
