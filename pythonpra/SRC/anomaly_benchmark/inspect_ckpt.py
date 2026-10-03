# 학습된 체크포인트로 이미지 폴더의 정상/불량을 판별하는 스크립트
"""
benchmark.py 로 학습해 checkpoints/ 에 저장된 체크포인트를 불러와 이미지 폴더를 판정한다.
재학습은 하지 않는다. (patchcore_real_inspect.py 를 세 모델·여러 장수용으로 일반화한 것)

동작 순서
    1) --model 과 --count 로 checkpoints/{model}_{count}.ckpt 를 고른다. (--ckpt 로 직접 지정도 가능)
       체크포인트에는 학습된 가중치와 판정 임계값이 들어 있다.
    2) 이미지 폴더의 이미지를 한 장씩 모델에 통과시켜 이상 맵과 이상 점수를 얻는다.
    3) 점수가 임계값을 넘으면 불량, 넘지 않으면 정상으로 판정한다.
    4) 판정표를 터미널에 출력하고, 이미지별 결과 그림을 results/inspect/{model}_{count}/ 에 저장한다.
    5) 저장한 결과 그림을 창에 한 장씩 띄운다. (아무 키 = 다음, q/ESC = 종료)

주의
    pred_score 는 체크포인트에 저장된 정규화·임계값 기준이라 모델 간 점수 크기를 직접 비교하지 않는다.
    모델 비교는 벤치마크 CSV 의 지표로 한다. 이상 맵 색은 이미지별 상대값이므로 판정은 점수와 라벨로 한다.

실행 예시
    python inspect_ckpt.py --model patchcore --count 300                      # real_images/ 폴더 판정
    python inspect_ckpt.py --model padim --count 100 --images dataset/hazelnut/test
    python inspect_ckpt.py --ckpt D:/x/model.ckpt --model patchcore --images D:/my_images
    python inspect_ckpt.py --model efficientad --count 300 --no-show          # 창 없이 파일만 저장
"""

import argparse
from pathlib import Path

# 경로, 환경 변수, 모델 팩토리, 해상도 상수는 공용 모듈의 것을 그대로 쓴다.
# (학습 때와 같은 설정으로 모델을 만들어야 체크포인트가 맞게 올라간다)
# common 을 import 하는 순간 작업 폴더가 anomaly_benchmark 로 바뀐다.
from common import (
    IMAGE_SIZE,
    INSPECT_DIR,
    MODEL_NAMES,
    REAL_DIR,
    PredictDataset,
    _as_list,
    _resize_map,
    build_engine,
    build_model,
    ckpt_path,
    np,
    run_tag,
)


# ----------------------------------------------------------------------
# 판별
# ----------------------------------------------------------------------
def inspect(args) -> None:
    """체크포인트로 이미지 폴더를 판정하고 결과를 출력·저장한다.

    출력
        터미널      이미지별 이상 점수와 판정, 전체 정상/불량 개수
        out 폴더    <파일명>_result.png (원본 / 이상 맵 / 겹친 결과)
    """
    import matplotlib

    matplotlib.use("Agg")  # 창 없이 파일로만 저장
    import matplotlib.pyplot as plt

    # 입력 확인 : 파일이 없으면 모델을 올리기 전에 바로 알려 준다.
    ckpt = Path(args.ckpt) if args.ckpt else ckpt_path(args.model, args.count)
    if not ckpt.exists():
        raise FileNotFoundError(
            f"체크포인트가 없다: {ckpt}\n"
            "benchmark.py 로 학습하면 checkpoints/{model}_{count}.ckpt 가 만들어진다."
        )
    images = Path(args.images)
    if not images.exists():
        raise FileNotFoundError(
            f"이미지 폴더가 없다: {images}\n"
            "--images 로 폴더를 지정한다. (예: dataset/hazelnut/test)"
        )
    tag = ckpt.stem if args.ckpt else run_tag(args.model, args.count)
    out_dir = Path(args.out) if args.out else INSPECT_DIR / tag
    print(f"모델       : {args.model}")
    print(f"체크포인트 : {ckpt}")
    print(f"이미지 폴더: {images}")

    # 체크포인트에 가중치와 판정 임계값이 들어 있으므로 불러오기만 하면 된다.
    # 이미지는 학습 때와 같은 해상도(common.IMAGE_SIZE)로 맞춘다. 크기가 다르면 결과가 어긋난다.
    dataset = PredictDataset(path=images, image_size=IMAGE_SIZE)
    # 모델은 빈 껍데기로 만들고, 내용은 ckpt_path 에서 채워진다.
    model = build_model(args.model)
    engine = build_engine(args.model, default_root_dir=out_dir / "_engine")
    predictions = engine.predict(model=model, dataset=dataset, ckpt_path=str(ckpt))

    out_dir.mkdir(parents=True, exist_ok=True)
    # anomalib 은 이미지 경로를 절대 경로로 돌려주므로 기준 폴더도 절대 경로로 맞춘다.
    images_root = (images if images.is_dir() else images.parent).resolve()

    rows = []  # (표시 이름, 점수, 판정)
    for batch in predictions:
        # 결과는 배치 단위로 온다. 필드별로 꺼내 이미지 한 장씩 처리한다.
        #   image_path  - 원본 파일 경로
        #   pred_score  - 이미지 이상 점수 (0~1 로 정규화, 클수록 이상)
        #   pred_label  - 임계값 적용 결과 (1 = 불량, 0 = 정상)
        #   anomaly_map - 위치별 이상 정도 (히트맵)
        paths = _as_list(batch.image_path)
        scores = _as_list(batch.pred_score)
        labels = _as_list(batch.pred_label)
        maps = batch.anomaly_map

        for i, path in enumerate(paths):
            # 하위 폴더가 있으면 폴더 이름을 붙여 구분한다. (crack/000.png 와 cut/000.png 가 겹치지 않게)
            rel = Path(path).relative_to(images_root).as_posix() if images.is_dir() else Path(path).name
            name = rel
            score = float(np.asarray(scores[i]).item())
            verdict = "불량" if int(np.asarray(labels[i]).item()) == 1 else "정상"
            rows.append((name, score, verdict))

            if maps is None:
                continue

            # 원본 / 이상 맵 / 겹친 결과를 한 장으로 저장
            anomaly_map = np.asarray(maps[i]).squeeze()
            image = plt.imread(path)
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            axes[0].imshow(image)
            axes[0].set_title("input")
            axes[1].imshow(anomaly_map, cmap="jet")
            axes[1].set_title("anomaly map")
            axes[2].imshow(image)
            # 이상 맵을 원본 크기로 늘려 반투명(alpha)으로 겹친다.
            axes[2].imshow(_resize_map(anomaly_map, image.shape[:2]), cmap="jet", alpha=0.45)
            # matplotlib 기본 폰트는 한글이 깨지므로 제목은 영문으로 쓴다.
            axes[2].set_title(f"{'DEFECT' if verdict == '불량' else 'NORMAL'}  score={score:.3f}")
            for ax in axes:
                ax.axis("off")
            fig.tight_layout()
            fig.savefig(out_dir / _result_name(name), dpi=120)
            plt.close(fig)  # 닫지 않으면 이미지 수만큼 메모리가 쌓인다.

    # 폴더, 파일명 숫자 순서로 정렬해서 출력 (1, 2, ..., 10)
    # 문자열 정렬만 하면 1, 10, 2 순서가 되므로 이름 길이를 먼저 비교한다.
    rows.sort(key=lambda r: (str(Path(r[0]).parent), len(Path(r[0]).stem), r[0]))
    width = max([len(r[0]) for r in rows] + [8]) + 2
    print(f"\n{'파일명':<{width}}{'이상 점수':>12}  판정")
    print("-" * (width + 18))
    for name, score, verdict in rows:
        print(f"{name:<{width}}{score:>12.4f}  {verdict}")

    # 요약 : 전체 / 정상 / 불량 개수
    n_bad = sum(1 for r in rows if r[2] == "불량")
    print("-" * (width + 18))
    print(f"전체 {len(rows)}장 / 정상 {len(rows) - n_bad}장 / 불량 {n_bad}장")
    print(f"결과 이미지 저장 위치: {out_dir.resolve()}")

    if args.no_show:
        return
    show_results(out_dir, rows, win=f"{args.model} result")


def _result_name(name: str) -> str:
    """표시 이름(crack/000.png) -> 결과 파일명(crack_000_result.png)."""
    p = Path(name)
    return "_".join([*p.parent.parts, p.stem]) + "_result.png"


# ----------------------------------------------------------------------
# 결과 보기
# ----------------------------------------------------------------------
def show_results(out_dir: Path, rows, win: str) -> None:
    """저장된 결과 이미지를 판정표 순서대로 한 장씩 창에 띄운다.

    조작
        아무 키      다음 이미지
        q / ESC      보기 종료
        창 닫기(X)   보기 종료
    """
    # matplotlib 은 위에서 파일 저장 전용(Agg)으로 바꿨으므로 창 표시는 OpenCV 로 한다.
    import cv2

    print("\n결과 이미지를 한 장씩 표시한다. 아무 키 = 다음, q/ESC = 종료")

    for i, (name, score, verdict) in enumerate(rows, start=1):
        path = out_dir / _result_name(name)
        if not path.exists():
            continue

        # cv2.imread 는 한글 경로를 못 읽으므로 바이트로 읽어서 디코딩한다.
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        try:
            cv2.imshow(win, image)
        except cv2.error:
            # opencv-python-headless 가 깔린 환경에서는 창을 못 띄운다. 결과 파일은 이미 저장됐다.
            print(
                "OpenCV 창을 띄울 수 없다. (GUI 가 없는 OpenCV 가 설치된 것으로 보인다)\n"
                f"결과 그림은 {out_dir} 에서 직접 열어 본다."
            )
            return
        # OpenCV 창 제목도 한글이 깨지므로 영문으로 쓴다.
        cv2.setWindowTitle(
            win, f"[{i}/{len(rows)}] {name}  {'DEFECT' if verdict == '불량' else 'NORMAL'}  score={score:.3f}"
        )

        # waitKey(0) 으로 무한 대기하면 창을 X 로 닫았을 때 멈춘다.
        # 짧게 기다리며 키 입력과 창 닫힘을 함께 확인한다.
        while True:
            key = cv2.waitKey(100)
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                cv2.destroyAllWindows()
                return
            if key != -1:
                break
        if key & 0xFF in (ord("q"), 27):  # 27 = ESC
            break

    cv2.destroyAllWindows()


# ----------------------------------------------------------------------
# 진입점
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """명령행 인자를 정의한다."""
    parser = argparse.ArgumentParser(
        description="체크포인트로 이미지 폴더 정상/불량 판별 (PaDiM / PatchCore / EfficientAD)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", required=True, choices=MODEL_NAMES, help="학습에 쓴 모델")
    parser.add_argument("--count", type=int, default=300, help="학습 장수 (checkpoints/{model}_{count}.ckpt)")
    parser.add_argument("--ckpt", default=None, help="체크포인트 경로를 직접 지정 (지정하면 --count 무시)")
    parser.add_argument("--images", default=str(REAL_DIR), help="판별할 이미지 폴더 (test 폴더도 가능)")
    parser.add_argument("--out", default=None, help="결과 저장 폴더 (기본: results/inspect/{model}_{count})")
    parser.add_argument("--no-show", action="store_true", help="OpenCV 창을 띄우지 않고 파일만 저장")
    return parser


if __name__ == "__main__":
    inspect(build_parser().parse_args())
