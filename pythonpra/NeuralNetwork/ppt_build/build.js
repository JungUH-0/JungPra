const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Food-11 Benchmark";
pres.title = "Food-11 이미지 분류 벤치마크";

// palette
const INK = "14181F";
const INK_SOFT = "2A3140";
const PAPER = "F7F5F2";
const CARD = "FFFFFF";
const MUTED = "6B7482";
const LIGHT = "B8BFC9";
const ACCENT = "16785C";        // 단일 액센트 (딥 틸)
const ACCENT_MID = "4A9C82";    // 차트 2번째 계열 — 같은 색상 계열의 밝은 톤
const ACCENT_PALE = "A8CFC2";   // 차트 저강도 톤
const ACCENT_ON_DARK = "4FC3A1"; // 어두운 배경 위 액센트
const LINE = "DDD9D2";

const KF = "Malgun Gothic"; // korean text
const NF = "Arial"; // numerals

const W = 13.3;
const M = 0.7; // margin

// ---------- helpers ----------
function darkBg(slide) {
  slide.background = { color: INK };
}
function lightBg(slide) {
  slide.background = { color: PAPER };
}

let pageNo = 0;
function newSlide(dark) {
  const s = pres.addSlide();
  pageNo++;
  s.background = { color: dark ? INK : PAPER };
  if (pageNo > 1) {
    s.addText(String(pageNo), {
      x: W - M - 0.7, y: 6.98, w: 0.7, h: 0.3,
      fontSize: 10.5, color: dark ? "6B7482" : MUTED, fontFace: NF,
      align: "right", isTextBox: true, margin: 0,
    });
  }
  return s;
}

function slideTitle(slide, text, sub) {
  slide.addText(text, {
    x: M, y: 0.45, w: W - M * 2, h: 0.65,
    fontSize: 32, bold: true, color: INK, fontFace: KF,
    isTextBox: true, margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: M, y: 1.12, w: W - M * 2, h: 0.36,
      fontSize: 13, color: MUTED, fontFace: KF,
      isTextBox: true, margin: 0,
    });
  }
}

function numCircle(slide, n, x, y, color, textColor) {
  slide.addShape(pres.ShapeType.ellipse, {
    x: x, y: y, w: 0.34, h: 0.34, fill: { color: color },
  });
  slide.addText(String(n), {
    x: x, y: y, w: 0.34, h: 0.34,
    fontSize: 13, bold: true, color: textColor || "FFFFFF", fontFace: NF,
    align: "center", valign: "middle", isTextBox: true, margin: 0,
  });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    fill: { color: fill || CARD }, rectRadius: 0.08,
    line: { color: LINE, width: 1 },
  });
}

function statBlock(slide, x, y, w, value, label, color) {
  slide.addText(value, {
    x: x, y: y, w: w, h: 0.85,
    fontSize: 48, bold: true, color: color, fontFace: NF,
    isTextBox: true, margin: 0,
  });
  slide.addText(label, {
    x: x, y: y + 0.82, w: w, h: 0.34,
    fontSize: 12, color: MUTED, fontFace: KF,
    isTextBox: true, margin: 0,
  });
}

function bullets(slide, items, x, y, w, h, size) {
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    {
      x: x, y: y, w: w, h: h,
      fontSize: size || 13, color: INK_SOFT, fontFace: KF,
      paraSpaceAfter: 8, isTextBox: true, margin: 0,
    }
  );
}

// ============ 1. TITLE ============
{
  const s = newSlide(true);

  s.addText("하이퍼파라미터에 정답은 없다", {
    x: M, y: 2.25, w: 11.9, h: 0.95,
    fontSize: 44, bold: true, color: "FFFFFF", fontFace: KF,
    isTextBox: true, margin: 0,
  });
  s.addText("Food-11 이미지 분류 — 구조가 바뀌면 최적값도 바뀐다", {
    x: M, y: 3.25, w: 11.9, h: 0.5,
    fontSize: 21, color: LIGHT, fontFace: KF,
    isTextBox: true, margin: 0,
  });

  s.addText("Keras · PyTorch 두 프레임워크로 각각 구현해 비교", {
    x: M, y: 4.05, w: 8.0, h: 0.35,
    fontSize: 14, color: ACCENT_ON_DARK, fontFace: KF, isTextBox: true, margin: 0,
  });

  s.addText("27개 조합 · 재현 실행 5회 · 최고 정확도 61.9%", {
    x: M, y: 6.2, w: 8, h: 0.35,
    fontSize: 13, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  s.addText("발표자 : 성명", {
    x: W - M - 4.6, y: 6.2, w: 4.6, h: 0.35,
    fontSize: 13, color: LIGHT, fontFace: KF,
    align: "right", isTextBox: true, margin: 0,
  });
  s.addNotes("Food-11 데이터셋으로 ANN, DNN, CNN 세 가지 구조를 Keras와 PyTorch 양쪽에서 구현하고, 옵티마이저와 정규화 기법을 바꿔가며 총 27개 조합을 비교했고, 그중 5개 조건은 재현 실행까지 진행한 실험입니다.");
}

// ============ 2. DATASET ============
{
  const s = newSlide(false);
  slideTitle(s, "데이터셋 — Food-11", "음식 사진 11개 카테고리 분류");

  // left stats
  card(s, M, 1.75, 5.1, 4.4);
  statBlock(s, M + 0.45, 2.1, 2.2, "11", "클래스 (음식 카테고리)", INK);
  statBlock(s, M + 0.45, 3.35, 3.5, "16,643", "학습·검증·평가 이미지", INK);
  statBlock(s, M + 0.45, 4.6, 3.5, "128×128", "리사이즈 후 입력 크기 (RGB)", INK);

  // right: selection criteria
  s.addText("이 데이터셋을 고른 이유", {
    x: 6.4, y: 1.85, w: 6.2, h: 0.4,
    fontSize: 17, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });

  const reasons = [
    ["적당한 난이도", "MNIST처럼 쉬우면 하이퍼파라미터를 바꿔도 차이가 안 보임"],
    ["train/val/eval 사전 분할", "직접 나눌 필요 없어 비교 조건이 일정하게 유지됨"],
    ["세 구조에 같은 형태로 입력", "고정 크기 이미지라 ANN·DNN·CNN에 그대로 사용 가능"],
    ["합리적인 학습 시간", "1.19GB 규모로 조합을 여러 번 반복 실험할 수 있음"],
  ];
  reasons.forEach((r, i) => {
    const y = 2.42 + i * 0.95;
    numCircle(s, i + 1, 6.4, y, INK_SOFT);
    s.addText(r[0], {
      x: 6.9, y: y - 0.03, w: 5.7, h: 0.3,
      fontSize: 14, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(r[1], {
      x: 6.9, y: y + 0.28, w: 5.7, h: 0.5,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });
  s.addText(
    [
      { text: "출처 : ", options: { color: MUTED, breakLine: false } },
      {
        text: "kaggle.com/datasets/trolukovich/food11-image-dataset",
        options: {
          color: MUTED,
          underline: false,
          breakLine: false,
          hyperlink: { url: "https://www.kaggle.com/datasets/trolukovich/food11-image-dataset" },
        },
      },
      { text: "  (EPFL Food-11 기반)", options: { color: MUTED } },
    ],
    {
      x: M, y: 6.4, w: 11.0, h: 0.3,
      fontSize: 10, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("난이도, 사전 분할, 입력 형태 통일, 학습 시간 네 가지 기준으로 Food-11을 선정했습니다. 원본은 EPFL에서 공개한 Food-11이고, 캐글 버전은 클래스별 폴더로 정리돼 있어 바로 사용할 수 있습니다.");
}

// ============ 3. EXPERIMENT DESIGN ============
{
  const s = newSlide(false);
  slideTitle(s, "실험 설계", "질문 — 같은 데이터에서 무엇을 바꿔야 성능이 움직이는가");

  card(s, M, 1.8, 5.75, 4.6);
  s.addText("고정한 조건", {
    x: M + 0.4, y: 2.1, w: 4.9, h: 0.4,
    fontSize: 17, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText("전 구간 동일하게 유지 — 통제 변수", {
    x: M + 0.4, y: 2.48, w: 4.9, h: 0.3,
    fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  bullets(s, [
    "이미지 크기 128×128×3",
    "배치 크기 32",
    "학습률 1e-3",
    "데이터셋 분할 (training / validation / evaluation)",
    "손실함수 cross-entropy",
  ], M + 0.4, 2.95, 4.9, 3.2, 13);

  card(s, 6.85, 1.8, 5.75, 4.6);
  s.addText("변화시킨 조건", {
    x: 7.25, y: 2.1, w: 4.9, h: 0.4,
    fontSize: 17, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText("단계별로 하나씩 추가 — 조작 변수", {
    x: 7.25, y: 2.48, w: 4.9, h: 0.3,
    fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  bullets(s, [
    "구조: ANN → DNN → CNN → Conv 블록 3개",
    "옵티마이저: SGD / SGD+momentum / Adam / AdamW",
    "epoch: 5 → 15 → 30(EarlyStopping)",
    "데이터 증강 적용 여부",
    "BatchNorm · He 초기화 · 학습률 스케줄링",
  ], 7.25, 2.95, 4.9, 3.2, 13);

  s.addNotes("학습률과 배치 크기는 통제 변수로 고정했습니다. 이 점은 뒤의 한계 슬라이드에서 다시 언급합니다.");
}

// ============ 4. ANN + DNN ============
{
  const s = newSlide(false);
  slideTitle(s, "출발점 — ANN과 DNN", "완전연결층만으로는 30%의 벽을 넘지 못했다");

  const groups = [
    {
      x: M,
      name: "ANN",
      desc: "은닉층 없음 · Flatten → Dense(11)",
      best: "21.3%",
      rows: [
        ["Keras", "SGD", "21.3%"],
        ["PyTorch", "SGD", "20.6%"],
        ["PyTorch", "Adam", "17.0%"],
        ["Keras", "Adam", "12.9%"],
      ],
    },
    {
      x: 6.85,
      name: "DNN",
      desc: "은닉층 2개 · 256 → 128",
      best: "26.9%",
      rows: [
        ["PyTorch", "Adam", "26.9%"],
        ["Keras", "SGD", "25.6%"],
        ["PyTorch", "SGD", "20.9%"],
        ["Keras", "Adam", "15.0%"],
      ],
    },
  ];

  groups.forEach((g) => {
    card(s, g.x, 1.8, 5.75, 3.3);
    s.addText(g.name, {
      x: g.x + 0.4, y: 1.98, w: 2.6, h: 0.42,
      fontSize: 21, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(g.desc, {
      x: g.x + 0.4, y: 2.4, w: 3.2, h: 0.3,
      fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(g.best, {
      x: g.x + 3.3, y: 1.95, w: 2.05, h: 0.7,
      fontSize: 34, bold: true, color: INK, fontFace: NF,
      align: "right", isTextBox: true, margin: 0,
    });
    s.addTable(
      [
        [
          { text: "프레임워크", options: { bold: true } },
          { text: "옵티마이저", options: { bold: true } },
          { text: "Test acc", options: { bold: true } },
        ],
        ...g.rows,
      ],
      {
        x: g.x + 0.4, y: 2.82, w: 4.95, colW: [1.7, 1.7, 1.55],
        fontSize: 11.5, fontFace: KF, color: INK_SOFT,
        border: { type: "solid", color: LINE, pt: 1 },
        fill: { color: CARD }, rowH: 0.34, valign: "middle",
        margin: 0.06,
      }
    );
  });

  const notes = [
    ["은닉층의 효과는 +5.6%p에 그쳤다", "무작위 추측(9.1%)의 두 배 남짓. 옵티마이저를 어떻게 바꿔도 두 구조 모두 30%를 넘지 못했다."],
    ["Adam 조합에서 loss가 치솟았다", "Keras ANN+Adam의 test loss는 7.93 — 정상 범위(2.4 부근)를 크게 벗어났다. 입력 49,152차원의 단순 선형 모델에서 Adam의 큰 보폭이 최적점을 지나친 것으로 보인다."],
  ];
  notes.forEach((n, i) => {
    const x = M + i * 6.15;
    numCircle(s, i + 1, x, 5.4, INK_SOFT);
    s.addText(n[0], {
      x: x + 0.48, y: 5.37, w: 5.3, h: 0.32,
      fontSize: 13.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(n[1], {
      x: x + 0.48, y: 5.72, w: 5.3, h: 0.95,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });
  s.addNotes("ANN과 DNN 모두 랜덤 추측보다는 낫지만 30%를 넘지 못했습니다. DNN에서 Keras는 SGD가, PyTorch는 Adam이 앞서 결론이 엇갈린 점은 단일 실행의 한계로 뒤에서 다시 다룹니다.");
}

// ============ 6. CNN LEAP ============
{
  const s = newSlide(false);
  slideTitle(s, "기준 모델 선정 — CNN", "이후의 하이퍼파라미터 실험은 모두 이 CNN 위에서 진행했다");

  const steps = [
    ["21.3%", "ANN", "은닉층 없음"],
    ["26.9%", "DNN", "은닉층 2개"],
    ["44.1%", "CNN", "Conv 블록 2개"],
  ];
  steps.forEach((st, i) => {
    const x = M + i * 4.2;
    s.addShape(pres.ShapeType.roundRect, {
      x: x, y: 2.55, w: 3.5, h: 2.5,
      fill: { color: i === 2 ? "E4F0EA" : CARD }, rectRadius: 0.1,
      line: { color: i === 2 ? ACCENT : LINE, width: 1 },
    });
    s.addText(st[0], {
      x: x + 0.35, y: 2.95, w: 2.8, h: 0.95,
      fontSize: 44, bold: true, color: i === 2 ? ACCENT : INK, fontFace: NF,
      isTextBox: true, margin: 0,
    });
    s.addText(st[1], {
      x: x + 0.35, y: 3.95, w: 2.8, h: 0.35,
      fontSize: 17, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(st[2], {
      x: x + 0.35, y: 4.32, w: 2.8, h: 0.35,
      fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
    if (i < 2) {
      s.addText("→", {
        x: x + 3.55, y: 3.5, w: 0.6, h: 0.5,
        fontSize: 24, color: "6B7482", fontFace: NF, align: "center",
        isTextBox: true, margin: 0,
      });
    }
  });

  s.addText(
    "이미지 분류에 CNN이 유리하다는 것은 이미 알려진 사실이다. 여기서 중요한 건 세 구조가 서로 다른 조건을 만들어낸다는 점 — 같은 옵티마이저가 ANN에서는 이기고 CNN에서는 지는 상황이 여기서부터 시작된다.",
    {
      x: M, y: 5.5, w: 11.9, h: 0.9,
      fontSize: 13.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("CNN이 이미지에 유리한 것은 교과서적 사실이므로 결론이 아니라 전제로 다룹니다. 이 슬라이드는 이후 하이퍼파라미터 실험의 무대를 설정하는 역할입니다.");
}

// ============ 7. OPTIMIZERS ============
{
  const s = newSlide(false);
  slideTitle(s, "옵티마이저 비교", "CNN 기본 구조, 5 epoch, 학습률 1e-3 고정");

  s.addChart(
    pres.ChartType.bar,
    [
      {
        name: "Keras",
        labels: ["Adam", "SGD + momentum", "SGD"],
        values: [43.6, 37.6, 25.5],
      },
      {
        name: "PyTorch",
        labels: ["Adam", "SGD + momentum", "SGD"],
        values: [44.1, 32.0, 20.5],
      },
    ],
    {
      x: M, y: 1.8, w: 7.2, h: 4.5,
      barDir: "col",
      chartColors: [ACCENT, ACCENT_PALE],
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelFontSize: 11,
      dataLabelColor: INK_SOFT,
      dataLabelFontFace: NF,
      showLegend: true,
      legendPos: "t",
      legendFontFace: KF,
      legendFontSize: 11,
      catAxisLabelColor: INK_SOFT,
      catAxisLabelFontSize: 11,
      catAxisLabelFontFace: KF,
      valAxisLabelColor: MUTED,
      valAxisLabelFontSize: 10,
      valAxisMaxVal: 55,
      valAxisMinVal: 0,
      valGridLine: { color: LINE, size: 1 },
      catGridLine: { style: "none" },
      barGapWidthPct: 60,
    }
  );

  card(s, 8.2, 1.8, 4.4, 4.5);
  s.addText("읽는 법", {
    x: 8.6, y: 2.05, w: 3.6, h: 0.35,
    fontSize: 16, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  const opt = [
    ["모델이 복잡할수록 Adam", "얕은 ANN에서는 SGD가 Adam을 이겼지만, CNN에서는 반대로 뒤집혔다"],
    ["모멘텀이 결정적", "순수 SGD는 5 epoch 안에 거의 제자리. momentum 0.9만 더해도 +12%p"],
    ["프레임워크는 무관", "같은 옵티마이저면 Keras·PyTorch 결과가 거의 일치한다"],
  ];
  opt.forEach((o, i) => {
    const y = 2.55 + i * 1.2;
    numCircle(s, i + 1, 8.6, y, INK_SOFT);
    s.addText(o[0], {
      x: 9.08, y: y - 0.03, w: 3.3, h: 0.3,
      fontSize: 13, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(o[1], {
      x: 9.08, y: y + 0.28, w: 3.3, h: 0.75,
      fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });
  s.addNotes("순수 SGD가 CNN에서 학습이 거의 진행되지 않은 것은 모멘텀 부재 때문입니다. 다만 학습률 1e-3은 Adam의 기본값이라 SGD에 불리했을 가능성이 있습니다.");
}

// ============ 8. OVERFITTING ============
{
  const s = newSlide(false);
  slideTitle(s, "과적합과 대응", "Adam으로 최고 성능을 냈더니 이번엔 다른 문제가 드러났다");

  // before
  card(s, M, 1.85, 5.75, 2.15);
  s.addText("문제 — Adam, 15 epoch", {
    x: M + 0.4, y: 2.08, w: 5.0, h: 0.35,
    fontSize: 15, bold: true, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "Train 93.2%", options: { bold: true, breakLine: false } },
      { text: "   vs   ", options: { color: MUTED, breakLine: false } },
      { text: "Test 45.4%", options: { bold: true } },
    ],
    {
      x: M + 0.4, y: 2.5, w: 5.0, h: 0.45,
      fontSize: 20, color: INK, fontFace: NF, isTextBox: true, margin: 0,
    }
  );
  s.addText("격차 47.8%p — 훈련 데이터를 외우기 시작. loss도 1.94 → 2.93으로 악화됐다.", {
    x: M + 0.4, y: 3.0, w: 5.0, h: 0.7,
    fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  // after
  card(s, 6.85, 1.85, 5.75, 2.15);
  s.addText("대응 후 — 증강 + EarlyStopping", {
    x: 7.25, y: 2.08, w: 5.0, h: 0.35,
    fontSize: 15, bold: true, color: ACCENT, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "Train 54.9%", options: { bold: true, breakLine: false } },
      { text: "   vs   ", options: { color: MUTED, breakLine: false } },
      { text: "Test 50.9%", options: { bold: true } },
    ],
    {
      x: 7.25, y: 2.5, w: 5.0, h: 0.45,
      fontSize: 20, color: INK, fontFace: NF, isTextBox: true, margin: 0,
    }
  );
  s.addText("격차 4.0%p — 정확도는 오르고 loss는 1.45로 개선. 14 epoch에서 자동 정지.", {
    x: 7.25, y: 3.0, w: 5.0, h: 0.7,
    fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  // methods
  s.addText("적용한 두 가지", {
    x: M, y: 4.3, w: 5.0, h: 0.35,
    fontSize: 16, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });

  const methods = [
    ["데이터 증강", "RandomFlip · RandomRotation · RandomZoom을 학습 시에만 적용해, 매 epoch 다른 이미지를 보게 만들어 암기를 어렵게 한다"],
    ["Early Stopping", "val_loss가 3회 연속 개선되지 않으면 학습을 멈추고, 가장 좋았던 시점의 가중치로 되돌린다"],
  ];
  methods.forEach((m, i) => {
    const x = M + i * 6.15;
    numCircle(s, i + 1, x, 4.85, INK_SOFT);
    s.addText(m[0], {
      x: x + 0.48, y: 4.82, w: 5.2, h: 0.3,
      fontSize: 13.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(m[1], {
      x: x + 0.48, y: 5.14, w: 5.2, h: 1.0,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });
  s.addNotes("증강을 넣으면 훈련 정확도가 오히려 낮아지는데, 이는 매 epoch 변형된 이미지를 보기 때문이며 실제 일반화 성능은 향상됩니다.");
}

// ---------- 그래프 자리 헬퍼 ----------
function graphSlot(slide, x, y, w, h, filename, caption) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    fill: { color: "FFFFFF" }, rectRadius: 0.06,
    line: { color: MUTED, width: 1, dashType: "dash" },
  });
  slide.addText(filename, {
    x: x, y: y + h / 2 - 0.34, w: w, h: 0.34,
    fontSize: 12.5, color: MUTED, fontFace: NF,
    align: "center", isTextBox: true, margin: 0,
  });
  slide.addText(caption, {
    x: x, y: y + h / 2 + 0.02, w: w, h: 0.3,
    fontSize: 10.5, color: MUTED, fontFace: KF,
    align: "center", isTextBox: true, margin: 0,
  });
}

// ============ 8-2. LEARNING CURVES — 과적합 ============
{
  const s = newSlide(false);
  slideTitle(s, "학습 곡선 — 증강 전후", "같은 구조인데 곡선 모양이 완전히 달라진다");

  const slots = [
    {
      x: M,
      file: "curve_keras1.png",
      cap: "증강 없음 · 15 epoch 고정",
      title: "문제 — 두 선이 벌어진다",
      body: "학습 정확도만 계속 오르고 검증 정확도는 40%대에서 멈춘다. 손실 그래프에서는 검증선이 3 epoch 이후 오히려 위로 꺾인다 — 모델이 훈련 데이터를 외우기 시작한 지점.",
    },
    {
      x: 6.85,
      file: "curve_keras2.png",
      cap: "증강 + EarlyStopping · 최대 30 epoch",
      title: "대응 — 두 선이 붙어서 간다",
      body: "증강으로 매 epoch 다른 이미지를 보게 하니 학습 정확도가 낮아지는 대신 두 선의 간격이 좁게 유지된다. 검증 손실이 더 이상 개선되지 않는 지점에서 자동 종료.",
    },
  ];

  slots.forEach((sl) => {
    graphSlot(s, sl.x, 1.85, 5.75, 2.15, sl.file, sl.cap);
    s.addText(sl.title, {
      x: sl.x, y: 4.2, w: 5.75, h: 0.35,
      fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(sl.body, {
      x: sl.x, y: 4.58, w: 5.75, h: 1.5,
      fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "숫자로는 Train 93.2% / Test 45.4% 같은 격차로만 보이지만, 곡선으로 보면 어느 epoch부터 갈라지기 시작했는지가 드러난다.",
    {
      x: M, y: 6.3, w: 11.9, h: 0.4,
      fontSize: 11.5, color: INK_SOFT, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("점선 상자 자리에 curve_keras1.png와 curve_keras2.png를 넣으세요. 왼쪽은 두 선이 벌어지고 오른쪽은 붙어서 가는 대비를 짚어주면 됩니다.");
}

// ============ 8-3. LEARNING CURVES — 프레임워크 ============
{
  const s = newSlide(false);
  slideTitle(s, "학습 곡선 — 두 프레임워크", "같은 조건이면 곡선의 모양도 닮는다");

  const slots = [
    { x: M, file: "curve_keras3.png", cap: "Keras · AdamW + ReduceLR", side: "Keras" },
    { x: 6.85, file: "curve_torch3.png", cap: "PyTorch · AdamW + ReduceLR", side: "PyTorch" },
  ];
  slots.forEach((sl) => {
    graphSlot(s, sl.x, 1.85, 5.75, 2.15, sl.file, sl.cap);
  });

  s.addText("곡선이 말해주는 것", {
    x: M, y: 4.25, w: 11.9, h: 0.35,
    fontSize: 16, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });

  const points = [
    ["수렴 속도는 다르다", "PyTorch가 더 이른 epoch에서 최저 검증 손실에 도달했다."],
    ["도달 지점은 비슷하다", "증강+EarlyStop 구간에서 두 프레임워크는 50.9%로 소수점까지 일치했다."],
    ["벌어졌다면 조건이 달랐다", "한때 19.6%p까지 벌어진 구간이 있었으나 BatchNorm과 ReLU 순서가 서로 달랐던 설정 실수였고, 맞추자 1.6%p로 좁혀졌다."],
  ];
  points.forEach((p, i) => {
    const x = M + i * 4.05;
    numCircle(s, i + 1, x, 4.75, INK_SOFT);
    s.addText(p[0], {
      x: x + 0.46, y: 4.72, w: 3.3, h: 0.3,
      fontSize: 12.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(p[1], {
      x: x + 0.46, y: 5.05, w: 3.3, h: 1.2,
      fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });
  s.addNotes("점선 상자에 curve_keras3.png와 curve_torch3.png를 넣으세요. 결론 3번(차이가 났다면 조건이 달랐던 것)의 근거가 되는 슬라이드입니다.");
}

// ============ 9. ARCHITECTURE IMPROVEMENT ============
{
  const s = newSlide(false);
  slideTitle(s, "구조 개선", "Conv 블록 추가 + BatchNorm + He 초기화");

  // layer flow
  const layers = [
    ["32", "채널", "126×126"],
    ["64", "채널", "61×61"],
    ["128", "채널", "28×28"],
  ];
  layers.forEach((l, i) => {
    const x = M + i * 2.6;
    s.addShape(pres.ShapeType.roundRect, {
      x: x, y: 1.9, w: 2.2, h: 1.45,
      fill: { color: CARD }, rectRadius: 0.08,
      line: { color: LINE, width: 1 },
    });
    s.addText(l[0], {
      x: x + 0.2, y: 2.05, w: 1.8, h: 0.6,
      fontSize: 28, bold: true, color: INK, fontFace: NF, isTextBox: true, margin: 0,
    });
    s.addText("채널 · " + l[2], {
      x: x + 0.2, y: 2.68, w: 1.8, h: 0.55,
      fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
    if (i < 2) {
      s.addText("→", {
        x: x + 2.22, y: 2.35, w: 0.4, h: 0.5,
        fontSize: 18, color: MUTED, fontFace: NF, align: "center",
        isTextBox: true, margin: 0,
      });
    }
  });

  card(s, 8.45, 1.9, 4.15, 1.45);
  statBlock(s, 8.85, 2.05, 3.4, "56.1%", "Keras · 기존 50.9% 대비 +5.2%p", ACCENT);

  // three additions
  const adds = [
    ["Conv 블록 3개", "32→64→128로 필터를 늘려 더 복잡한 시각 패턴을 학습"],
    ["BatchNorm", "각 블록 출력을 재조정해 층이 깊어져도 학습이 안정적으로 유지"],
    ["He 초기화", "ReLU가 신호 절반을 죽이는 것을 보상해 가중치를 √(2/입력수)로 시작"],
  ];
  adds.forEach((a, i) => {
    const x = M + i * 4.05;
    card(s, x, 3.7, 3.75, 2.55);
    numCircle(s, i + 1, x + 0.4, 3.95, INK_SOFT);
    s.addText(a[0], {
      x: x + 0.4, y: 4.45, w: 3.0, h: 0.35,
      fontSize: 14, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(a[1], {
      x: x + 0.4, y: 4.82, w: 3.0, h: 1.3,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "He 초기화는 Keras에서만 명시했다 — PyTorch의 Conv2d·Linear는 기본값이 이미 Kaiming(He) 계열이기 때문.",
    {
      x: M, y: 6.45, w: 11.9, h: 0.4,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("두 프레임워크의 초기화 기본값이 다르기 때문에 같은 He 초기화에 도달하려고 서로 다른 조치를 했습니다.");
}

// ============ 9-2. CNN STEP-BY-STEP ============
{
  const s = newSlide(false);
  slideTitle(s, "CNN 개선 경로", "무엇을 더할 때마다 결과가 어떻게 움직였는가");

  s.addTable(
    [
      [
        { text: "단계", options: { bold: true } },
        { text: "추가한 것", options: { bold: true } },
        { text: "Keras", options: { bold: true } },
        { text: "PyTorch", options: { bold: true } },
        { text: "관찰", options: { bold: true } },
      ],
      ["① 기본 CNN (5 epoch)", "Conv 블록 2개", "43.6%", "44.1%", "DNN 대비 +17%p"],
      ["② epoch 15", "학습 시간 3배", "45.4%", "44.0%", "거의 제자리, 과적합만 심화"],
      ["③ + 증강 + EarlyStop", "과적합 대응", "50.9%", "50.9%", "두 프레임워크 정확히 일치"],
      ["④ + 3Conv · BatchNorm · He", "구조 개선", "56.1%", "54.5%", "구조가 아직 남은 지렛대였음"],
      [
        "⑤ + AdamW + ReduceLR",
        "옵티마이저 · 스케줄링",
        { text: "52.1%", options: { color: MUTED } },
        { text: "59.2%", options: { color: ACCENT, bold: true } },
        "정반대로 갈림",
      ],
    ],
    {
      x: M, y: 1.85, w: 11.9, colW: [2.85, 2.5, 1.5, 1.5, 3.55],
      fontSize: 11.5, fontFace: KF, color: INK_SOFT,
      border: { type: "solid", color: LINE, pt: 1 },
      fill: { color: CARD }, rowH: 0.42, valign: "middle",
      margin: 0.07,
    }
  );

  const obs = [
    ["학습 시간만 늘리는 건 효과 없다", "②단계에서 epoch을 3배로 늘렸지만 test는 1.8%p 오르는 데 그쳤고, train은 93.2%까지 치솟아 과적합만 깊어졌다."],
    ["가장 확실한 도약은 과적합 대응", "③단계에서 두 프레임워크가 나란히 50.9%로 올라섰다. 소수점까지 일치한 유일한 구간으로, 조건이 맞으면 프레임워크는 결과에 영향을 주지 않는다는 근거."],
    ["마지막 단계에서 결론이 갈렸다", "같은 AdamW 변경인데 Keras는 하락, PyTorch는 상승. 두 CNN의 분류 헤드가 달랐던 것(Dropout 유무)이 원인으로 추정된다."],
  ];
  obs.forEach((o, i) => {
    const x = M + i * 4.05;
    card(s, x, 4.75, 3.8, 1.85);
    numCircle(s, i + 1, x + 0.32, 4.98, INK_SOFT);
    s.addText(o[0], {
      x: x + 0.32, y: 5.42, w: 3.2, h: 0.3,
      fontSize: 12.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(o[1], {
      x: x + 0.32, y: 5.74, w: 3.2, h: 0.8,
      fontSize: 10, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "②단계는 Keras가 Adam, PyTorch가 SGD+momentum으로 서로 다른 옵티마이저를 확장했다 — 이 행만 직접 비교 대상이 아니다.",
    {
      x: M, y: 6.72, w: 11.0, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("CNN 내부에서 다섯 단계를 거치며 44%에서 59%까지 올라간 경로입니다. 각 단계가 무엇을 해결했는지 설명하면서 진행하면 좋습니다.");
}

// ============ 10. FINAL RESULT ============
{
  const s = newSlide(false);
  slideTitle(s, "전체 요약", "ANN에서 최종 모델까지, 단계별로 무엇이 성능을 움직였나");

  s.addChart(
    pres.ChartType.bar,
    [
      {
        name: "Test accuracy",
        labels: ["ANN", "DNN", "CNN", "CNN\n+증강+ES", "CNN\n3Conv+BN", "최종\nAdamW"],
        values: [21.3, 26.9, 44.1, 50.9, 56.1, 61.9],
      },
    ],
    {
      x: M, y: 1.85, w: 7.5, h: 4.4,
      barDir: "col",
      chartColors: ["C3CBD3", "AFBFC4", ACCENT_PALE, "8FC4B2", ACCENT_MID, ACCENT],
      varyColors: true,
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelFontSize: 12,
      dataLabelColor: INK_SOFT,
      dataLabelFontFace: NF,
      showLegend: false,
      catAxisLabelColor: INK_SOFT,
      catAxisLabelFontSize: 10.5,
      catAxisLabelFontFace: KF,
      valAxisLabelColor: MUTED,
      valAxisLabelFontSize: 10,
      valAxisMaxVal: 70,
      valAxisMinVal: 0,
      valGridLine: { color: LINE, size: 1 },
      catGridLine: { style: "none" },
      barGapWidthPct: 45,
    }
  );

  card(s, 8.5, 1.85, 4.1, 2.05);
  statBlock(s, 8.9, 2.15, 3.3, "61.9%", "PyTorch · AdamW + ReduceLR", ACCENT);

  s.addText("최고 기록의 근거", {
    x: 8.5, y: 4.15, w: 4.1, h: 0.35,
    fontSize: 14, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText(
    "이 조건은 두 번 돌려 59.2%와 61.9%가 나왔다. 같은 구조를 Adam으로 돌린 두 실행(54.5% · 52.6%)보다 모두 높아 범위가 겹치지 않는다.\n\nPyTorch에는 Dropout이 없어 weight decay가 그 빈 자리를 채운 것으로 보인다. 이미 Dropout(0.5)이 있던 Keras에서는 같은 변경이 아무 차이도 만들지 않았다.",
    {
      x: 8.5, y: 4.55, w: 4.1, h: 1.8,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("정규화는 기법을 더할수록 좋아지는 것이 아니라, 모델에 이미 걸린 정규화 총량에 달린 문제라는 해석입니다. 단일 실행이므로 가설 수준으로 제시합니다.");
}

// ============ 10-2. REPRODUCIBILITY ============
{
  const s = newSlide(false);
  slideTitle(s, "재현 실행 — 우리 결론을 검증하다", "곡선을 남기려 다시 돌렸더니, 결론 하나가 갈렸다");

  s.addTable(
    [
      [
        { text: "조건", options: { bold: true } },
        { text: "1차", options: { bold: true } },
        { text: "2차", options: { bold: true } },
        { text: "편차", options: { bold: true } },
      ],
      ["Keras · 2Conv · Adam", "45.4%", "46.4%", "1.8%p"],
      ["Keras · 3Conv+BN · Adam", "56.1%", "52.5%", "3.6%p"],
      ["Keras · 3Conv+BN · AdamW", "52.1%", "56.7%", "4.6%p"],
      ["PyTorch · 3Conv+BN · Adam", "54.5%", "52.6%", "6.1%p"],
      [
        "PyTorch · 3Conv+BN · AdamW",
        "59.2%",
        { text: "61.9%", options: { color: ACCENT, bold: true } },
        "2.7%p",
      ],
    ],
    {
      x: M, y: 1.85, w: 6.6, colW: [3.0, 1.2, 1.2, 1.2],
      fontSize: 11.5, fontFace: KF, color: INK_SOFT,
      border: { type: "solid", color: LINE, pt: 1 },
      fill: { color: CARD }, rowH: 0.4, valign: "middle",
      margin: 0.07,
    }
  );

  card(s, 7.4, 1.85, 5.2, 2.4);
  s.addText("같은 설정, 다시 돌렸을 때", {
    x: 7.8, y: 2.08, w: 4.4, h: 0.32,
    fontSize: 13, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText("최대 6.1%p", {
    x: 7.8, y: 2.42, w: 4.4, h: 0.75,
    fontSize: 38, bold: true, color: INK, fontFace: NF, isTextBox: true, margin: 0,
  });
  s.addText(
    "5%p 안팎의 차이는 단독 실행 하나로 주장할 수 없다는 기준선이 실측으로 생겼다.",
    {
      x: 7.8, y: 3.22, w: 4.4, h: 0.85,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );

  const findings = [
    [
      "절반은 노이즈였다",
      "\"Keras에서 AdamW가 4%p 떨어뜨렸다\"는 관찰은 재현되지 않았다. 두 조건 평균이 54.3% 대 54.4%로 사실상 동일 — 1차에서 우연히 한쪽이 높게 나온 것이었다.",
    ],
    [
      "절반은 더 단단해졌다",
      "PyTorch의 AdamW 이득은 재현됐다. 두 실행(59.2 · 61.9)이 Adam 두 실행(54.5 · 52.6)보다 모두 높아 범위가 겹치지 않는다. 평균 +7.0%p.",
    ],
    [
      "결론을 지운 게 아니라 다듬었다",
      "\"프레임워크마다 정반대\"에서 \"정규화가 부족한 모델에서만 효과\"로. 검증을 거친 뒤 남은 주장이 처음보다 정확해졌다.",
    ],
  ];
  findings.forEach((f, i) => {
    const x = M + i * 4.05;
    card(s, x, 4.5, 3.8, 1.9);
    numCircle(s, i + 1, x + 0.32, 4.72, i === 2 ? ACCENT : INK_SOFT);
    s.addText(f[0], {
      x: x + 0.32, y: 5.16, w: 3.2, h: 0.3,
      fontSize: 12.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(f[1], {
      x: x + 0.32, y: 5.48, w: 3.2, h: 0.85,
      fontSize: 10, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "곡선 기록이 목적이었지만, 결과적으로 각 조건을 2회씩 돌린 재현성 실험이 됐다 — 다음 장의 한계 ③에 대한 직접적인 답변이다.",
    {
      x: M, y: 6.55, w: 11.9, h: 0.35,
      fontSize: 11, color: INK_SOFT, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("결론을 방어하지 않고 스스로 검증해 걸러냈다는 점을 강조하세요. 편차 6.1%p라는 실측치가 이 발표에서 가장 단단한 숫자입니다.");
}

// ============ 11. LIMITATIONS ============
{
  const s = newSlide(false);
  slideTitle(s, "실험의 한계", "결과를 해석할 때 함께 고려해야 할 점");

  const lims = [
    ["SGD에 불리한 학습률", "전 구간 lr=1e-3으로 고정했으나 이는 Adam의 기본값이다. SGD의 일반적 기본값은 1e-2로 10배 크다."],
    ["두 CNN의 구조 불일치", "Keras는 Flatten→Dropout→Dense, PyTorch는 Flatten→Linear(128)→Linear로 헤드가 달랐다."],
    ["단일 실행 결과 (부분 해소)", "26개 조합을 1회씩만 돌렸다. 다만 5개 조건을 재현해 편차가 최대 6.1%p임을 실측했고, 그 결과 결론 하나를 수정했다 — 앞 장 참고."],
    ["test set 반복 관찰", "26회 실행마다 test 정확도를 확인했다. 선택 과정에 test 정보가 일부 새어 들어갔다."],
    ["미탐색 하이퍼파라미터", "배치 크기와 학습률 자체는 한 번도 바꾸지 않았다. 둘 다 영향력이 큰 변수다."],
  ];

  lims.forEach((l, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = M + col * 6.15;
    const y = 1.9 + row * 1.55;
    numCircle(s, i + 1, x, y, INK_SOFT);
    s.addText(l[0], {
      x: x + 0.48, y: y - 0.03, w: 5.3, h: 0.3,
      fontSize: 14, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(l[1], {
      x: x + 0.48, y: y + 0.3, w: 5.3, h: 1.05,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "후속 과제 — SGD를 lr=1e-2로 재실험, 두 프레임워크의 헤드 구조 통일, 조합별 3회 반복 후 평균 비교",
    {
      x: M, y: 6.35, w: 11.9, h: 0.45,
      fontSize: 12.5, bold: true, color: INK_SOFT, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("한계를 먼저 밝히면 결과의 신뢰도가 올라갑니다. 특히 SGD 학습률 문제는 질문이 나올 가능성이 높습니다.");
}

// ============ 12. WHY THE CEILING ============
{
  const s = newSlide(false);
  slideTitle(s, "왜 62%에서 멈췄나", "남은 격차는 튜닝이 아니라 접근법의 문제");

  card(s, M, 1.85, 5.75, 1.5);
  s.addText("61.9%", {
    x: M + 0.4, y: 2.05, w: 2.3, h: 0.75,
    fontSize: 40, bold: true, color: INK, fontFace: NF, isTextBox: true, margin: 0,
  });
  s.addText("이번 실험 — 사전학습 없이 밑바닥부터 학습", {
    x: M + 0.4, y: 2.82, w: 5.0, h: 0.35,
    fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  card(s, 6.85, 1.85, 5.75, 1.5);
  s.addText("85~90%", {
    x: 7.25, y: 2.05, w: 3.2, h: 0.75,
    fontSize: 40, bold: true, color: ACCENT, fontFace: NF, isTextBox: true, margin: 0,
  });
  s.addText("전이학습 — ImageNet 사전학습 모델을 미세조정할 때 일반적으로 보고되는 범위", {
    x: 7.25, y: 2.82, w: 5.0, h: 0.45,
    fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  const causes = [
    ["사전학습 없음", "랜덤 가중치에서 시작해 \"엣지란 무엇인가\"부터 전부 스스로 배워야 했다. 격차의 대부분이 여기서 나온다."],
    ["클래스당 900장", "밑바닥 학습에는 매우 적은 양. 증강으로 변형을 늘려도 원본이 담은 정보량 자체는 늘지 않는다."],
    ["문제 자체가 어렵다", "\"빵\" 하나에 바게트·식빵·샌드위치가 다 들어가고, 밥과 면처럼 사람도 헷갈리는 경계가 있다."],
    ["해상도 128×128", "음식 구분에 중요한 질감 단서가 마지막 Conv에서 14×14까지 축소되며 상당 부분 사라진다."],
  ];
  causes.forEach((c, i) => {
    const x = M + i * 3.05;
    card(s, x, 3.65, 2.75, 2.45);
    numCircle(s, i + 1, x + 0.32, 3.9, INK_SOFT);
    s.addText(c[0], {
      x: x + 0.32, y: 4.38, w: 2.15, h: 0.35,
      fontSize: 13.5, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.32, y: 4.74, w: 2.15, h: 1.25,
      fontSize: 10.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "이번 튜닝(21% → 62%)은 밑바닥 학습이라는 조건 안에서 뽑아낼 수 있는 것을 거의 다 뽑아낸 결과 — 다음 단계는 튜닝이 아니라 전이학습으로 접근법을 바꾸는 것이다.",
    {
      x: M, y: 6.35, w: 11.9, h: 0.5,
      fontSize: 12.5, bold: true, color: INK_SOFT, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("\"왜 59%밖에 안 되나요\"라는 질문에 대한 답변 슬라이드입니다. 성능 상한이 하이퍼파라미터가 아니라 사전학습 유무와 데이터 규모에서 온다는 점을 설명합니다.");
}

// ============ 13. CONCLUSION ============
{
  const s = newSlide(true);

  s.addText("결론", {
    x: M, y: 0.85, w: 11.9, h: 0.75,
    fontSize: 34, bold: true, color: "FFFFFF", fontFace: KF, isTextBox: true, margin: 0,
  });

  const concl = [
    ["최적 옵티마이저는 모델에 따라 뒤집힌다", "얕은 ANN에서는 순수 SGD가 Adam을 21.3% 대 12.9%로 앞섰지만, CNN에서는 Adam이 44.1% 대 20.5%로 압도했다. momentum 0.9를 더하는 것만으로 +12%p가 움직이기도 했다. \"일단 Adam\"이라는 기본값은 성립하지 않았다."],
    ["정규화는 더하기가 아니라 총량의 문제", "각 조건을 2회씩 돌린 결과, AdamW의 weight decay는 Dropout이 없던 PyTorch에서 53.6% → 60.6%(+7.0%p)를 만들었고 이미 Dropout(0.5)이 있던 Keras에서는 54.3% → 54.4%로 아무 차이도 없었다. 부족한 곳은 채우고, 충분한 곳에는 보탤 것이 없다."],
    ["차이가 났다면 조건이 달랐던 것이다", "조건을 맞춘 구간에서 두 프레임워크는 50.9%로 소수점까지 일치했다. 19.6%p까지 벌어졌던 구간은 BatchNorm과 ReLU 순서가 서로 달랐던 설정 실수였고, 바로잡자 1.6%p로 좁혀졌다."],
  ];

  concl.forEach((c, i) => {
    const y = 2.05 + i * 1.5;
    numCircle(s, i + 1, M, y, ACCENT_ON_DARK, INK);
    s.addText(c[0], {
      x: M + 0.5, y: y - 0.05, w: 11.3, h: 0.35,
      fontSize: 18, bold: true, color: "FFFFFF", fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(c[1], {
      x: M + 0.5, y: y + 0.35, w: 11.3, h: 0.85,
      fontSize: 12.5, color: LIGHT, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText("Food-11 · 27개 조합 · 재현 실행 5회 · 최고 정확도 61.9%", {
    x: M, y: 6.5, w: 11.9, h: 0.4,
    fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addNotes("세 가지 결론으로 마무리합니다. 질문은 전체 실험 기록 페이지를 띄워두고 답변하면 좋습니다.");
}

pres.writeFile({ fileName: "food11_presentation.pptx" }).then(() => {
  console.log("saved food11_presentation.pptx");
});
