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

  s.addText(
    [
      { text: "모델 구조와 학습 조건에 따른 성능 비교", options: { breakLine: true } },
      { text: "Food-11 이미지 분류", options: {} },
    ],
    {
      x: M, y: 2.05, w: 11.9, h: 2.0,
      fontSize: 28, color: LIGHT, fontFace: KF,
      isTextBox: true, margin: 0,
    }
  );

  s.addText("Keras · PyTorch 두 프레임워크로 각각 구현해 비교", {
    x: M, y: 4.05, w: 8.0, h: 0.35,
    fontSize: 14, color: ACCENT_ON_DARK, fontFace: KF, isTextBox: true, margin: 0,
  });

  s.addText("실험한 30개 조합 중 최고 정확도 61.9% · 재현 실행 6회", {
    x: M, y: 6.2, w: 8, h: 0.35,
    fontSize: 13, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });

  s.addText("발표자 : 정의형", {
    x: W - M - 4.6, y: 6.2, w: 4.6, h: 0.35,
    fontSize: 13, color: LIGHT, fontFace: KF,
    align: "right", isTextBox: true, margin: 0,
  });
  s.addNotes("Food-11 데이터셋으로 ANN, DNN, CNN 세 가지 구조를 Keras와 PyTorch 양쪽에서 구현하고, 옵티마이저와 정규화 기법을 바꿔가며 총 30개 조합을 비교했고, 그중 6개 조건은 재현 실행까지 진행한 실험입니다.");
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
  slideTitle(s, "실험 설계", "같은 데이터에서 무엇을 바꿔야 성능이 움직이는가");

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

  s.addText(
    "두 구현은 각 프레임워크의 공식 예제를 기준으로 작성했다 — 그 결과 분류 헤드가 서로 달라졌고, 그 차이가 얼마나 컸는지는 학습 곡선 비교에서 다룬다.",
    {
      x: M, y: 6.55, w: 11.9, h: 0.35,
      fontSize: 11, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("학습률과 배치 크기는 통제 변수로 고정했습니다. 이 점은 뒤의 한계 슬라이드에서 다시 언급합니다. 하단 한 줄을 꼭 짚고 넘어가세요 — 뒤에서 Keras와 PyTorch를 계속 나란히 비교하는데, 두 모델의 분류 헤드가 애초에 달랐다는 사실을 여기서 미리 밝혀두는 것입니다. 이걸 안 밝히면 옵티마이저 비교 슬라이드에서 \"두 모델 구조는 같나요\"라는 질문이 나왔을 때 뒤로 미뤄야 하고, 앞 슬라이드들의 신뢰가 흔들립니다. 미리 말해두면 오히려 알고 측정했다는 인상이 됩니다.");
}

// ============ 4. ANN + DNN ============
{
  const s = newSlide(false);
  slideTitle(s, "출발점 — ANN과 DNN");

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
    ["은닉층의 효과는 +5.6%p에 그쳤다", ""],
    ["Adam 조합에서 loss가 치솟았다", ""],
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
  slideTitle(s, "기준 모델 선정 — CNN");

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
    ["이 차트는 5 epoch 시점", "얕은 ANN에서는 SGD가 Adam을 앞섰다. 여기 보이는 Adam의 우위는 epoch을 늘리면 좁혀진다"],
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

// ---------- 학습 곡선 헬퍼 ----------
const CURVES = "../curves/"; // build.js 기준 상대 경로

function curvePair(slide, leftFile, leftCap, rightFile, rightCap) {
  const pos = [
    { x: M, file: leftFile, cap: leftCap },
    { x: 6.85, file: rightFile, cap: rightCap },
  ];
  pos.forEach((p) => {
    slide.addImage({ path: CURVES + p.file, x: p.x, y: 1.72, w: 5.75, h: 2.13 });
    const body = Array.isArray(p.cap)
      ? [
          { text: p.cap[0], options: { fontSize: 11.5, bold: true, color: INK, breakLine: true } },
          { text: p.cap[1], options: { fontSize: 8.5, bold: false, color: MUTED } },
        ]
      : p.cap;
    slide.addText(body, {
      x: p.x, y: 3.9, w: 5.75, h: Array.isArray(p.cap) ? 0.42 : 0.3,
      fontSize: 11.5, bold: true, color: INK, fontFace: KF,
      align: "center", isTextBox: true, margin: 0,
    });
  });
}

// ============ 7-2. CURVE 1 — OPTIMIZER ============
{
  const s = newSlide(false);
  slideTitle(s, "학습 곡선 — 옵티마이저", "구조·epoch·데이터를 모두 고정하고 옵티마이저만 바꿨을 때");

  curvePair(
    s,
    "curve_torch1_adam.png", "PyTorch · Adam — 4 epoch에 정점, 이후 val loss 발산",
    "curve_torch4.png", "PyTorch · SGD + momentum — 15 epoch에도 상승 중"
  );

  s.addTable(
    [
      [
        { text: "2 Conv · 15 epoch · 증강 없음", options: { bold: true } },
        { text: "Train", options: { bold: true } },
        { text: "Test", options: { bold: true } },
        { text: "Test loss", options: { bold: true } },
      ],
      ["Keras · Adam", "93.6%", "46.4%", { text: "3.08", options: { color: MUTED } }],
      ["Keras · SGD + momentum", "68.7%", "43.1%", { text: "1.80", options: { color: ACCENT, bold: true } }],
      ["PyTorch · Adam", "99.4%", "44.4%", { text: "4.81", options: { color: MUTED } }],
      ["PyTorch · SGD + momentum", "57.0%", "43.0%", { text: "1.66", options: { color: ACCENT, bold: true } }],
    ],
    {
      x: M, y: 4.28, w: 6.4, colW: [2.8, 1.2, 1.2, 1.2],
      fontSize: 11.5, fontFace: KF, color: INK_SOFT,
      border: { type: "solid", color: LINE, pt: 1 },
      fill: { color: CARD }, rowH: 0.36, valign: "middle", margin: 0.07,
    }
  );

  s.addText("Adam은 일찍 멈췄고, SGD는 계속 올라왔다", {
    x: 7.4, y: 4.28, w: 5.2, h: 0.35,
    fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText(
    "epoch을 3배로 늘리자 Adam은 +0.3~1.8%p, SGD+momentum은 +5.5~12.0%p 올랐다.\n\n격차를 좁힌 쪽은 SGD였고, Train은 42%p·test loss는 2.9배 벌어졌다.",
    {
      x: 7.4, y: 4.75, w: 5.2, h: 1.6,
      fontSize: 14, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("5 epoch에서 15 epoch로 늘렸을 때 각자 얼마나 올랐는지가 핵심입니다 — Keras Adam 43.6→45.4(+1.8), Keras SGD+mom 37.6→43.1(+5.5), PyTorch Adam 44.1→44.4(+0.3), PyTorch SGD+mom 32.0→44.0(+12.0). 3배의 시간을 받고 Adam은 거의 안 올랐고, 격차가 좁혀진 것은 전부 SGD가 올라왔기 때문입니다. 왜 Adam이 멈췄는지는 다음다음 장 곡선에 있습니다 — keras1의 검증 손실이 3 epoch에서 최저(1.71)를 찍고 3.35까지 단조 상승합니다. 즉 Adam은 도착한 것이 아니라 일찍 과적합에 들어간 것이고, 남은 epoch은 전부 암기로 갔습니다(train 93.2%). 반대로 SGD+momentum은 15 epoch에도 아직 상승 중이라 최종 도달점은 측정하지 못했습니다 — 그래서 'SGD가 더 낫다'까지는 말하지 마세요. 6번 막대 차트가 5 epoch 시점이라는 점도 여기서 짚어주면 좋습니다.");
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

// ============ 8-2. CURVE 2 — AUGMENTATION ============
{
  const s = newSlide(false);
  slideTitle(s, "학습 곡선 — 과적합 대응 전후", "같은 프레임워크, 과적합 대응 전과 후");

  curvePair(
    s,
    "curve_keras1.png", "증강 없음 · 15 epoch 고정",
    "curve_keras2.png", "증강 + EarlyStopping · 3 Conv + BatchNorm"
  );

  const pair = [
    [
      M,
      "두 선이 벌어진다",
      "학습 정확도만 계속 올라 93.6%에 이르고 검증 정확도는 40%대에서 멈춘다. 손실 그래프에서는 검증선이 3 epoch에서 최저(1.71)를 찍은 뒤 3.35까지 단조 상승 — 이 지점부터 외우기 시작했다.",
    ],
    [
      6.85,
      "두 선이 붙어서 간다",
      "증강으로 매 epoch 다른 이미지를 보게 하니 학습 정확도가 60%대로 낮아지는 대신 두 선의 간격이 좁게 유지된다. 검증 손실이 개선을 멈춘 지점에서 자동 종료.",
    ],
  ];
  pair.forEach((p) => {
    s.addText(p[1], {
      x: p[0], y: 4.35, w: 5.75, h: 0.35,
      fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(p[2], {
      x: p[0], y: 4.75, w: 5.75, h: 1.6,
      fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addNotes("왼쪽은 두 선이 벌어지고 오른쪽은 붙어서 가는 대비를 짚어주면 됩니다. 오른쪽은 구조도 3 Conv+BatchNorm으로 바뀌었으므로 증강만의 효과는 아니라는 점을 밝히세요.");
}

// ============ 9. ARCHITECTURE IMPROVEMENT ============
{
  const s = newSlide(false);
  slideTitle(s, "구조 및 학습 안정화 기법 적용", "Conv 블록 추가 + BatchNorm + He 초기화");

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

// ============ 9-2. CURVE 4 — EARLYSTOP PITFALL ============
{
  const s = newSlide(false);
  slideTitle(s, "EarlyStopping이 놓친 지점", "val_loss 0.006 차이로 검증 정확도 3.5%p를 잃었다");

  s.addImage({ path: CURVES + "curve_torch2.png", x: 1.4, y: 1.75, w: 10.5, h: 3.89 });

  s.addTable(
    [
      [
        { text: "PyTorch · 3 Conv+BN · Adam · EarlyStop p=5", options: { bold: true } },
        { text: "val_loss", options: { bold: true } },
        { text: "val_acc", options: { bold: true } },
      ],
      ["epoch 5 — 복원된 가중치", { text: "1.494", options: { color: ACCENT, bold: true } }, "51.2%"],
      ["epoch 8 — 실제 최고 정확도", "1.500", { text: "54.7%", options: { color: ACCENT, bold: true } }],
    ],
    {
      x: M, y: 5.85, w: 6.6, colW: [3.6, 1.5, 1.5],
      fontSize: 11, fontFace: KF, color: INK_SOFT,
      border: { type: "solid", color: LINE, pt: 1 },
      fill: { color: CARD }, rowH: 0.32, valign: "middle", margin: 0.06,
    }
  );

  s.addText(
    "monitor=\"val_loss\"로 최적 시점을 고른 결과, loss가 0.006 낮다는 이유로 정확도가 3.5%p 낮은 지점이 선택됐다. BatchNorm이 검증 지표를 흔드는 구간에서는 val_accuracy를 함께 보는 편이 안전하다.",
    {
      x: 7.5, y: 5.85, w: 5.1, h: 1.0,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("실무형 함정 사례입니다. 시간이 부족하면 이 슬라이드를 부록으로 돌려도 발표는 성립합니다.");
}

// ============ 9-3. CURVE 3 — FRAMEWORK ============
{
  const s = newSlide(false);
  slideTitle(s, "학습 곡선 — 두 프레임워크", "같은 학습 설정에서도 모델 구현 차이로 학습 경로가 달라졌다");

  curvePair(
    s,
    "curve_keras1.png", ["Keras · Dropout 있음 · 파라미터 65만", "(Keras Simple MNIST convnet 참고)"],
    "curve_torch1_adam.png", ["PyTorch · Dropout 없음 · 파라미터 739만", "(PyTorch Quickstart 참고)"]
  );

  s.addTable(
    [
      [
        { text: "2 Conv · Adam · 15 epoch", options: { bold: true } },
        { text: "Train", options: { bold: true } },
        { text: "Test", options: { bold: true } },
        { text: "Test loss", options: { bold: true } },
      ],
      ["Keras", "93.6%", "46.4%", "3.08"],
      ["PyTorch", { text: "99.4%", options: { color: MUTED, bold: true } }, "44.4%", { text: "4.81", options: { color: MUTED, bold: true } }],
    ],
    {
      x: M, y: 4.35, w: 6.4, colW: [2.8, 1.2, 1.2, 1.2],
      fontSize: 11.5, fontFace: KF, color: INK_SOFT,
      border: { type: "solid", color: LINE, pt: 1 },
      fill: { color: CARD }, rowH: 0.38, valign: "middle", margin: 0.07,
    }
  );

  s.addText("도착점은 같고, 가는 길이 달랐다", {
    x: 7.4, y: 4.35, w: 5.2, h: 0.35,
    fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addText(
    "Test acc 46.4% 대 44.4% — 차이는 작다.\n\nPyTorch는 train 99.4% · val loss 4.81로 과적합이 심하다.\n\n원인은 헤드 구조 — Dropout 유무와 파라미터 11.3배 차이.",
    {
      x: 7.4, y: 4.75, w: 5.2, h: 1.9,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("Keras는 Flatten→Dropout→Dense(11)로 65만 파라미터, PyTorch는 은닉 Linear(57600,128)가 하나 더 있어 739만 — 11.3배입니다. 이 헤드 차이는 임의로 바꾼 게 아니라 각 프레임워크 공식 예제를 그대로 따른 결과입니다(Keras mnist_convnet에는 Dropout이 있고 PyTorch quickstart에는 없습니다). Conv 부분은 채널 수까지 맞췄습니다. 결론 ②·③의 근거이자, PyTorch 모델이 실제로 정규화가 부족했다는 직접 증거입니다. 주의 — Keras의 train 93.6%는 Dropout이 켜진 상태로 측정된 값이라 실제 용량 차이는 이보다 작습니다.");
}

// ============ 9-4. CNN STEP-BY-STEP ============
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
      ["② epoch 15", "학습 시간 3배", "45.4%", "44.4%", "거의 제자리, 과적합만 심화"],
      ["③ + 증강 + EarlyStop", "과적합 대응", "50.9%", "50.9%", "두 프레임워크 정확히 일치"],
      ["④ + 3Conv · BatchNorm · He", "구조 개선", "56.1%", "54.5%", "구조가 아직 남은 지렛대였음"],
      [
        "⑤ + AdamW + ReduceLR",
        "옵티마이저 · 스케줄링",
        { text: "52.1%", options: { color: MUTED } },
        { text: "59.2%", options: { color: ACCENT, bold: true } },
        "Keras 하락은 재현 안 됨",
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
    ["학습 시간만 늘리는 건 효과 없다", "epoch 3배에 test는 +1.8%p, train만 93.2%까지 치솟았다."],
    ["가장 확실한 도약은 과적합 대응", "두 프레임워크가 나란히 50.9% — 소수점까지 일치한 유일한 구간."],
    ["다시 돌려보고 해석이 바뀐 단계", "1차엔 정반대로 보였지만, 두 번씩 돌리자 Keras 하락은 편차였다."],
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
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "④단계 조건에서 PyTorch를 SGD+momentum으로 돌리면 56.1% — 같은 조건 Adam 두 실행(54.5 · 52.6)보다 높았다. 구조가 커지자 옵티마이저 우열이 사라졌다.",
    {
      x: M, y: 6.72, w: 11.9, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("CNN 내부에서 다섯 단계를 거쳐 44%에서 61.9%까지 올라간 경로입니다. 카드별로 덧붙일 내용 — ① ②단계는 epoch을 3배로 늘렸는데 test는 1.8%p뿐이고 train이 93.2%까지 올라 과적합만 깊어졌습니다. ② ③단계의 50.9%는 두 프레임워크가 소수점까지 일치한 유일한 구간이라, 조건이 맞으면 프레임워크는 결과에 영향을 주지 않는다는 근거가 됩니다. ③ ⑤단계는 1차만 보면 Keras 하락·PyTorch 상승으로 정반대였는데, 각 조건을 두 번씩 돌리자 Keras 쪽 하락은 실행 편차였고(평균 54.3% 대 54.4%) PyTorch 쪽 상승만 남았습니다. 다섯 단계 모두 Keras·PyTorch 양쪽 다 Adam으로 맞춘 값이라 행마다 직접 비교가 됩니다(②단계 PyTorch 44.4%는 나중에 따로 돌린 Adam 실행입니다). 하단 각주는 표에 없는 30번째 조합입니다 — ④단계와 같은 조건에서 옵티마이저만 SGD+momentum으로 바꾸니 56.1%가 나왔고, Adam 두 실행보다 모두 높았습니다. 다만 SGD 쪽은 1회 실행이라 최고 Adam 실행(54.5%)과의 차이 1.6%p는 측정 편차(4.6%p) 안입니다. 'SGD가 이겼다'가 아니라 '구조가 커지니 차이가 사라졌다'까지만 말하세요.");
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
    "이 조건은 두 번 돌려 59.2%와 61.9%가 나왔다. 같은 구조를 Adam으로 돌린 두 실행(54.5% · 52.6%)보다 모두 높아 범위가 겹치지 않는다.\n\n여섯 조건을 두 번씩 돌려 test 정확도가 최대 4.6%p까지 흔들린다는 것도 함께 측정했다 — 이 발표에서 차이가 있다고 말할 수 있는 기준선이다.",
    {
      x: 8.5, y: 4.55, w: 4.1, h: 2.1,
      fontSize: 11.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    }
  );
  s.addNotes("정규화는 기법을 더할수록 좋아지는 것이 아니라, 모델에 이미 걸린 정규화 총량에 달린 문제라는 해석입니다. 여섯 조건을 2회씩 재현해 범위가 겹치지 않는 것까지 확인했으므로 가설이 아니라 근거를 갖춘 주장으로 말해도 됩니다. 재현 실행 표 전체는 결과 페이지에 있으니 질문이 나오면 그때 띄우세요.");
}

// ============ 11. LIMITATIONS ============
{
  const s = newSlide(false);
  slideTitle(s, "실험의 한계", "결론별로, 어떤 근거가 아직 약한가");

  const lims = [
    ["두 CNN이 같은 모델이 아니었다", "결론 ② ③", "파라미터 653K 대 7.39M — 11.3배. Dropout 유무만의 문제가 아니다."],
    ["한 단계에서 변수를 여러 개 바꿨다", "결론 ②", "④⑤단계가 각각 세 개씩. AdamW의 몫만 떼어낼 수 없다."],
    ["61.9%는 35번 측정 중 최댓값이다", "최고 기록", "학습·검증·평가는 분리했지만, 35번의 결과를 보며 조건을 정했다. 2회 평균은 60.6%다."],
    ["SGD에 불리했을 수 있는 학습률", "결론 ①", "lr=1e-3은 Adam 기본값. 다만 momentum이 유효 보폭을 10배로 키운다."],
  ];

  lims.forEach((l, i) => {
    const y = 2.15 + i * 1.12;
    numCircle(s, i + 1, M, y, INK_SOFT);
    s.addText(l[0], {
      x: M + 0.5, y: y - 0.02, w: 4.3, h: 0.4,
      fontSize: 16, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(l[2], {
      x: 5.7, y: y - 0.02, w: 5.1, h: 0.75,
      fontSize: 12.5, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(l[1], {
      x: 10.95, y: y + 0.02, w: 1.65, h: 0.3,
      fontSize: 11, bold: true, color: ACCENT, fontFace: KF,
      align: "right", isTextBox: true, margin: 0,
    });
  });

  s.addNotes("한계를 결론별로 묶은 것이 핵심입니다. 각 항목에 덧붙일 내용 — ① PyTorch 헤드에만 Linear(57600,128)이 있어 파라미터가 11.3배입니다. 증강 회전 폭(±36° 대 ±10°)과 EarlyStop patience(3 대 5)도 어긋나 있었습니다. 결론 ②의 \"Dropout이 없어서\"가 유일한 원인이 아닐 수 있다는 뜻입니다. ② ④단계는 Conv 블록·BatchNorm·He를, ⑤단계는 AdamW·ReduceLR·patience(3→7)를 함께 바꿨습니다. ReduceLR이 실제로 발동했는지도 확인하지 않았습니다. ③ 분할 자체는 지켰습니다 — 학습은 training, EarlyStopping은 validation, evaluation은 실행 끝에 한 번뿐입니다. 다만 35회의 test 결과를 보며 다음 조건을 정했고(patience 3→5 변경이 그 예), 61.9%는 그중 최댓값입니다. 인용할 때 단서를 붙이세요. ④ 질문이 나올 가능성이 가장 높습니다. momentum 0.9가 유효 보폭을 lr/(1-0.9) = 10배로 키워 lr=1e-2를 근사하고, 그 조건에서 SGD가 43.0~43.1%로 Adam과 동률이었다는 점까지 답하면 방어가 아니라 근거 제시가 됩니다.");
}

// ============ 12. WHY THE CEILING ============
{
  const s = newSlide(false);
  slideTitle(s, "이번 실험에서는 61.9%에서 멈춘 이유", "하이퍼파라미터로는 좁히기 어려운 조건들");

  const causes = [
    ["사전학습 없음", "랜덤 가중치에서 시작해 \"엣지란 무엇인가\"부터 전부 스스로 배워야 했다. 격차의 대부분이 여기서 나온다."],
    ["클래스당 900장", "밑바닥 학습에는 매우 적은 양. 증강으로 변형을 늘려도 원본이 담은 정보량 자체는 늘지 않는다."],
    ["문제 자체가 어렵다", "\"빵\" 하나에 바게트·식빵·샌드위치가 다 들어가고, 밥과 면처럼 사람도 헷갈리는 경계가 있다."],
    ["해상도 128×128", "음식 구분에 중요한 질감 단서가 마지막 Conv에서 14×14까지 축소되며 상당 부분 사라진다."],
  ];
  causes.forEach((c, i) => {
    const x = M + i * 3.05;
    card(s, x, 1.9, 2.75, 4.05);
    numCircle(s, i + 1, x + 0.32, 2.2, INK_SOFT);
    s.addText(c[0], {
      x: x + 0.32, y: 2.8, w: 2.11, h: 0.72,
      fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.32, y: 3.58, w: 2.11, h: 2.2,
      fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addNotes("\"왜 61.9%밖에 안 되나요\"라는 질문에 대한 답변 슬라이드입니다. 네 가지 모두 옵티마이저나 epoch을 바꿔서는 좁히기 어려운 조건이라는 점을 짚으세요. 화면에는 원인만 있으니 마무리는 말로 하세요 — '이 네 가지는 하이퍼파라미터로 줄일 수 없는 조건이고, 다음 단계는 튜닝이 아니라 사전학습 모델을 미세조정하는 전이학습입니다.' 정도면 충분합니다. 다만 \"여기가 한계입니다\"라고 단정하지 마세요 — 학습률과 배치 크기는 한 번도 바꾸지 않았고(15번 한계), 이 실험은 한 가지 구조 계열만 다뤘습니다. 전이학습이 유력해 보인다는 것도 문헌에서 알려진 방향이지 저희가 측정한 결과는 아니라고 밝히는 편이 안전합니다. 확인한 것과 추정한 것을 구분해 말하는 것이 이 슬라이드의 핵심입니다.");
}

// ============ 12-2. FUTURE WORK ============
{
  const s = newSlide(false);
  slideTitle(s, "추가 하이퍼파라미터 실험 — 확장 가능성", "이번 실험에서 고정했거나 충분히 분리하지 못한 조건");

  const next = [
    ["학습률", "현재 1e-3으로 고정. 1e-4·3e-4·1e-3·3e-3처럼 범위를 나눠 옵티마이저별 적정 학습률을 비교할 수 있다."],
    ["배치 크기", "현재 32로 고정. 16·32·64를 비교해 학습 안정성, 속도, 일반화 성능이 어떻게 달라지는지 확인할 수 있다."],
    ["정규화 강도", "Dropout 비율과 weight decay를 독립적으로 조정해 과적합 억제 효과를 분리해서 측정할 수 있다."],
    ["증강 강도", "회전·확대·이동 범위를 단계적으로 바꿔 어느 수준까지 일반화에 도움이 되고, 언제 정보 손실이 커지는지 비교할 수 있다."],
  ];
  next.forEach((c, i) => {
    const x = M + i * 3.05;
    card(s, x, 1.9, 2.75, 4.05);
    numCircle(s, i + 1, x + 0.32, 2.2, INK_SOFT);
    s.addText(c[0], {
      x: x + 0.32, y: 2.8, w: 2.11, h: 0.72,
      fontSize: 15, bold: true, color: INK, fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.32, y: 3.58, w: 2.11, h: 2.2,
      fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addNotes("15번 한계에서 밝힌 것들을 어떻게 풀지로 이어가는 장입니다. 가장 먼저 할 일은 앞 장에서 말한 헤드 구조 통일이고, 그 위에서 이 네 가지를 봅니다. 하단 한 줄이 핵심입니다 — 이번 실험의 가장 큰 방법론적 약점이 한 단계에서 여러 변수를 동시에 바꾼 것과 조합당 1회 실행이었으므로, 다음 실험은 그 둘을 먼저 고쳐야 합니다.");
}

// ============ 13. CONCLUSION ============
{
  const s = newSlide(true);

  s.addText("결론", {
    x: M, y: 0.85, w: 11.9, h: 0.75,
    fontSize: 34, bold: true, color: "FFFFFF", fontFace: KF, isTextBox: true, margin: 0,
  });

  const concl = [
    ["같은 예산을 주자 옵티마이저의 우열이 사라졌다", "epoch 3배에 Adam은 +0.3~1.8%p, SGD+momentum은 +5.5~12.0%p 올라 격차가 좁혀졌다."],
    ["정규화는 더하기가 아니라 총량의 문제였다", "AdamW + ReduceLR 조합은 Dropout이 없던 PyTorch에서 +7.0%p, 이미 Dropout이 있던 Keras에서는 거의 변화가 없었다."],
    ["차이가 났다면 조건이 달랐던 것이다", "조건을 맞춘 구간에서 두 프레임워크는 50.9%로 소수점까지 일치했다."],
  ];

  concl.forEach((c, i) => {
    const y = 2.25 + i * 1.45;
    numCircle(s, i + 1, M, y, ACCENT_ON_DARK, INK);
    s.addText(c[0], {
      x: M + 0.5, y: y - 0.08, w: 11.3, h: 0.42,
      fontSize: 21, bold: true, color: "FFFFFF", fontFace: KF, isTextBox: true, margin: 0,
    });
    s.addText(c[1], {
      x: M + 0.5, y: y + 0.42, w: 11.3, h: 0.62,
      fontSize: 14, color: LIGHT, fontFace: KF, isTextBox: true, margin: 0,
    });
  });

  s.addText("Food-11 · 30개 실험 · 재현 실행 6회 · 실험한 조합 중 최고 정확도 61.9%", {
    x: M, y: 6.5, w: 11.9, h: 0.4,
    fontSize: 12, color: MUTED, fontFace: KF, isTextBox: true, margin: 0,
  });
  s.addNotes("세 줄만 읽고, 아래 근거는 질문이 나올 때 꺼내세요. ① 얕은 ANN에서는 순수 SGD가 21.3% 대 12.9%로 Adam을 앞섰고, CNN 5 epoch에서는 Adam이 12.1%p 앞섰습니다. epoch을 15로 늘리자 Adam은 +0.3~1.8%p밖에 못 올랐고 SGD+momentum이 +5.5~12.0%p 올라와 격차가 사라졌습니다(네 실행 모두 43.0~46.4%, 측정 편차 4.6%p 안). Adam이 멈춘 이유는 3 epoch부터 과적합에 들어갔기 때문입니다. 다만 SGD 쪽은 15 epoch에도 상승 중이라 최종 도달점은 모릅니다. ② 두 조건을 2회씩 돌린 평균입니다 — PyTorch Adam 53.6% → AdamW 60.6%, Keras 54.3% → 54.4%. PyTorch에는 Dropout이 없고 헤드 파라미터가 11배 많았습니다. ③ 19.6%p까지 벌어졌던 구간은 BatchNorm과 ReLU 순서가 달랐던 설정 실수였고, 맞추자 1.6%p로 좁혀졌습니다. 질문은 결과 페이지(아티팩트)를 띄워두고 답변하세요.");
}

pres.writeFile({ fileName: "food11_presentation.pptx" }).then(() => {
  console.log("saved food11_presentation.pptx");
});
