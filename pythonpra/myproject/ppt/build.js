// 개인 AI 비서 — 발표 자료 소스 (.pptx는 산출물). 내용 근거는 ../DEVLOG.md
// 덱이 두 가지다. 기존 덱은 그대로 두고, 과정 중심 덱을 추가로 만든다.
//   assistant_devlog.pptx  시행착오로 보는 개발 과정 (13장)
//   assistant_process.pptx 문제 정의에서 검증까지, 선택한 이유 (13장, 약 9분 50초)
// 파일명은 버전 없이 하나씩 (이력은 git이 보관).
// 사용자가 PowerPoint에서 직접 고친 내용이 있을 수 있으니, 덮어쓰기 전에 저장된 pptx와 먼저 비교할 것.
//   npm install pptxgenjs
//   node build.js            기존 덱만
//   node build.js process    과정 중심 덱만
//   node build.js all        둘 다
const pptxgen = require("pptxgenjs");

let pres; // 덱마다 새로 만든다 (newDeck)
function newDeck(title) {
  pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  pres.author = "개인 AI 비서";
  pres.title = title;
}

// ── palette ─────────────────────────────────────────────
const INK = "1B2230";        // 지배색 (어두운 남색)
const PAPER = "F5F6F8";
const CARD = "FFFFFF";
const MUTED = "6A7384";
const FAIL = "C8443A";       // 문제 / 실패
const FAIL_PALE = "FBE9E7";
const OK = "1F8A70";         // 해결 / 채택
const OK_PALE = "E3F3EE";
const HOLD = "B7791F";       // 보류
const HOLD_PALE = "FBF1DC";
const FONT = "Malgun Gothic";

const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 });

function text(slide, t, x, y, w, h, o = {}) {
  slide.addText(t, Object.assign({
    x, y, w, h, fontFace: FONT, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true,
  }, o));
}

function card(slide, x, y, w, h, fill = CARD, withShadow = true) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill, width: 0 },
    shadow: withShadow ? shadow() : undefined,
  });
}

// 모든 내용 슬라이드 공통 머리글: 제목만 (v2에서 영역 태그 제거)
function header(slide, title) {
  slide.background = { color: PAPER };
  text(slide, title, 0.6, 0.67, 12.1, 0.7, { fontSize: 32, bold: true });
}

// 제목 줄 오른쪽 위 "사용 모델 / 이름" 상자 (LLM 슬라이드의 어두운 패널과 같은 색)
function techBadge(slide, label, name, note) {
  const x = 8.4, y = 0.4, w = 4.3, h = note ? 1.15 : 0.95;
  card(slide, x, y, w, h, INK, false);
  text(slide, label, x + 0.3, y + 0.15, w - 0.6, 0.3, { fontSize: 13, bold: true, color: "F2B8B2" });
  text(slide, name, x + 0.3, y + 0.45, w - 0.6, 0.4, { fontSize: 18, bold: true, color: "FFFFFF" });
  if (note) text(slide, note, x + 0.3, y + 0.82, w - 0.6, 0.25, { fontSize: 12, color: "C9D0DD" });
}

// 라벨 + 본문 (카드 안 텍스트)
function labeled(slide, x, y, w, h, label, body, labelColor, ls = 17, bs = 16) {
  text(slide, [
    { text: label, options: { fontSize: ls, bold: true, color: labelColor, breakLine: true } },
    { text: body, options: { fontSize: bs, color: INK } },
  ], x, y, w, h, { paraSpaceAfter: 4 });
}

// ── 1. 표지 ─────────────────────────────────────────────
function slideCover(subtitle, notes) {
  const s = pres.addSlide();
  s.background = { color: INK };
  text(s, "개인 AI 비서", 0.9, 2.2, 11.5, 1.0, { fontSize: 54, bold: true, color: "FFFFFF" });
  text(s, subtitle || "시행착오로 보는 개발 과정", 0.9, 3.35, 11.5, 0.7, { fontSize: 30, color: "C9D0DD" });
  text(s, "손동작 · 음성 · 포즈를 로컬 LLM으로 해석해서 PC를 제어한다", 0.9, 4.5, 11.5, 0.5, { fontSize: 18, color: "9AA4B6" });
  s.addNotes(notes || "[0:20 / 누적 0:20] 인사와 한 줄 소개. 전체 발표 시간은 약 10분.");
  return s;
}

// ── 2. 목적 (목표 · 출발 + 만든 순서) ───────────────────
function slidePurpose(notes) {
  const s = pres.addSlide();
  header(s, "목적");
  s.addNotes(notes || "[1:00 / 누적 1:20] 만든 이유를 먼저 말한다. 목표: 클릭과 예/아니오를 뺀 모든 동작을 사용자가 직접 정의. 수어 인식 프로젝트에서 MediaPipe 손 인식을 써 본 뒤 추가 활용법을 찾다가 시작. 오른쪽은 만든 순서를 한 번만 훑는다.");
  card(s, 0.6, 2.0, 4.9, 4.6, INK, false);
  text(s, "목표", 0.9, 2.3, 4.3, 0.4, { fontSize: 15, bold: true, color: "F2B8B2" });
  text(s, "클릭과 예/아니오를 뺀 모든 동작을 사용자가 직접 정의한다", 0.9, 2.75, 4.3, 1.4, { fontSize: 20, bold: true, color: "FFFFFF" });
  text(s, "출발", 0.9, 4.3, 4.3, 0.4, { fontSize: 15, bold: true, color: "9ADBC6" });
  text(s, "수어 인식 프로젝트의 손 인식에서 출발, 추가 활용법을 찾다가 비서로", 0.9, 4.75, 4.3, 1.6, { fontSize: 15, color: "C9D0DD" });

  text(s, "만든 순서 (커밋 기준)", 5.8, 1.85, 6.9, 0.35, { fontSize: 14, bold: true, color: MUTED });
  const steps = [
    ["로컬 LLM 도입", "명령을 문장으로 등록"],
    ["손 안정화", "오발동 제거, 명령 종류 확장"],
    ["음성 명령", "웨이크워드 · 손등으로 녹음해 실행"],
    ["포즈 · 모드 전환", "손과 포즈를 번갈아 사용"],
  ];
  steps.forEach((st, i) => {
    const y = 2.3 + i * 1.05;
    card(s, 5.8, y, 6.9, 0.9);
    text(s, [
      { text: st[0], options: { bold: true, color: OK } },
      { text: "   " + st[1], options: { color: INK } },
    ], 6.05, y, 6.4, 0.9, { fontSize: 15, valign: "middle" });
  });
  return s;
}

// ── 3. 처리 흐름 (입력 → 처리 → 출력, 한 줄) ───────────
function slideFlow(notes) {
  const s = pres.addSlide();
  header(s, "처리 흐름");
  s.addNotes(notes || "[1:00 / 누적 2:20] 입력에서 출력까지 한 줄로 설명한다. 인식 모듈은 동작의 이름만 넘기고 실행은 다른 곳이 맡는다. LLM이 만든 값은 허용 목록에 있는 것만 실행한다. 손과 포즈는 한 번에 하나만 켠다.");
  const stages = [
    { title: "카메라\n마이크", desc: "", value: "영상 · 소리" },
    { title: "인식", desc: "손 · 포즈 · 음성", value: "동작 이름 ·\n받아쓴 문장" },
    { title: "연결", desc: "main.py\n모드 전환\n명령 찾기", value: "명령 또는 문장" },
    { title: "해석 · 검증", desc: "commandmodule\n해석\n허용 목록 검사", value: "{ action, target }" },
    { title: "실행", desc: "windowcontrol\n마우스 · 키 · 창", value: "" },
  ];
  const w = 2.1, gap = 0.4, x0 = 0.6, y = 2.3, h = 3.2;
  // 입력 / 처리 / 출력 묶음 표시
  const groupX = (i) => x0 + i * (w + gap);
  text(s, "입력", groupX(0), 1.85, w, 0.35, { fontSize: 14, bold: true, color: MUTED, align: "center" });
  text(s, "처리", groupX(1), 1.85, groupX(3) + w - groupX(1), 0.35, { fontSize: 14, bold: true, color: MUTED, align: "center" });
  text(s, "출력", groupX(4), 1.85, w, 0.35, { fontSize: 14, bold: true, color: MUTED, align: "center" });
  stages.forEach((st, i) => {
    const x = groupX(i);
    card(s, x, y, w, h, i === 0 || i === 4 ? OK_PALE : CARD, i > 0 && i < 4);
    text(s, st.title, x + 0.2, y + 0.2, w - 0.4, 0.8, { fontSize: 18, bold: true });
    if (st.desc) text(s, st.desc, x + 0.2, y + 1.0, w - 0.4, 1.3, { fontSize: 14, color: MUTED });
    if (st.value) {
      text(s, "넘기는 값", x + 0.2, y + 2.2, w - 0.4, 0.25, { fontSize: 12, color: MUTED });
      text(s, st.value, x + 0.2, y + 2.45, w - 0.4, 0.6, { fontSize: 14, bold: true, color: OK });
    }
    if (i < stages.length - 1) text(s, "→", x + w, y, gap, h, { fontSize: 24, color: MUTED, align: "center", valign: "middle" });
  });
  const principles = [
    ["인식은 이름만 넘긴다", "명령을 바꿔도 인식 코드는 그대로"],
    ["허용 목록만 실행한다", "목록에 없으면 거부"],
    ["한 번에 하나만 켠다", "손 ↔ 포즈는 양손 모으기로 전환"],
  ];
  const nw = (12.1 - 0.4) / 3;
  principles.forEach((n, i) => {
    const x = 0.6 + i * (nw + 0.2);
    card(s, x, 5.75, nw, 1.2, i === 1 ? HOLD_PALE : OK_PALE, false);
    labeled(s, x + 0.25, 5.87, nw - 0.5, 1.0, n[0], n[1], i === 1 ? HOLD : OK, 16, 14);
  });
  return s;
}

// ── 4. 도구 (용도별 · 출처 · 상태) ──────────────────────
function slideTools(notes) {
  const s = pres.addSlide();
  header(s, "도구");
  s.addNotes(notes || "[0:50 / 누적 3:10] 용도별로 어떤 도구를 썼는지, 지금 상태가 어떤지 한 번에 본다. 모델은 출처 링크를 붙였다. 박수는 별도 모델 없이 소리 크기 변화로 감지한다.");
  const head = ["영역", "용도", "도구 · 모델", "상태", "출처"].map((t) => ({
    text: t, options: { bold: true, color: "FFFFFF", fill: { color: INK }, fontSize: 14 },
  }));
  const link = (label, url) => ({ text: label, options: { fontSize: 12, hyperlink: { url } } });
  const plain = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: INK }, o) });
  const status = (t, c) => ({ text: t, options: { fontSize: 14, bold: true, color: c } });
  const rows = [
    ["손", "손 21개 점 인식", "MediaPipe Hands · OpenCV", status("완성", OK), link("github.com/google-ai-edge/mediapipe", "https://github.com/google-ai-edge/mediapipe")],
    ["눈", "눈 감김 비율(EAR)", "MediaPipe Face Mesh", status("제외", HOLD), plain("위와 동일", { color: MUTED, fontSize: 12 })],
    ["포즈", "상체 키포인트 인식", "MediaPipe Pose", status("등록 예정", HOLD), plain("위와 동일", { color: MUTED, fontSize: 12 })],
    ["음성", "음성 → 텍스트", "faster-whisper medium", status("구현", OK), link("huggingface.co/Systran/faster-whisper-medium", "https://huggingface.co/Systran/faster-whisper-medium")],
    ["LLM", "문장 → 동작", "Qwen2.5-3B-Instruct (Ollama)", status("구현", OK), link("huggingface.co/Qwen/Qwen2.5-3B-Instruct", "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct")],
    ["박수", "소리 크기 변화", "sounddevice · NumPy (모델 없음)", status("전환에서 제외", HOLD), plain("—", { color: MUTED })],
    ["PC 제어", "마우스 · 키보드 · 창", "pywin32", status("완성", OK), link("github.com/mhammond/pywin32", "https://github.com/mhammond/pywin32")],
  ].map((r) => r.map((c) => (typeof c === "string" ? plain(c, c === r[0] ? { bold: true } : {}) : c)));
  s.addTable([head, ...rows], {
    x: 0.6, y: 1.95, w: 12.1, colW: [1.2, 2.6, 3.2, 1.7, 3.4], rowH: 0.56,
    fontFace: FONT, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1],
    border: { type: "solid", pt: 0.75, color: "DDE0E6" }, fill: { color: CARD },
  });
  return s;
}

// ── 5. 개발 방식 (LLM 활용) ─────────────────────────────
function slideDevMethod(notes) {
  const s = pres.addSlide();
  header(s, "개발 방식");
  s.addNotes(notes || "[0:50 / 누적 4:00] 이 프로젝트는 Claude Code 세션으로 코드를 만들고 조언을 받으며 진행했다. 코드 작성과 수정, 설계 조언, 로그를 보고 원인 가설을 세우는 일에 썼다. 제품 안의 Qwen과는 별개.");
  text(s, "LLM(Claude Code)", 0.6, 1.85, 6, 0.35, { fontSize: 14, bold: true, color: MUTED });
  const items = [
    ["코드 작성 · 수정", "모듈 구현과 오류 수정\n(예: 예외 처리)"],
    ["설계 조언", "구조 제안과 대안 비교\n(예: 명령 모듈 공유)"],
    ["원인 분석 보조", "로그를 읽고 원인 가설 제시\n(예: pinch_middle, 박수)"],
  ];
  const w = 3.8, gap = 0.35;
  items.forEach((it, i) => {
    const x = 0.6 + i * (w + gap);
    card(s, x, 2.3, w, 2.4);
    labeled(s, x + 0.3, 2.6, w - 0.6, 1.9, it[0], it[1], INK, 20, 17);
  });
  return s;
}

// ── 5. 손: 커서 · 우클릭 · 휠 ───────────────────────────
function slideHand(notes) {
  const s = pres.addSlide();
  header(s, "손");
  s.addNotes(notes || "[0:50 / 누적 4:50] 시도, 문제, 해결 순서로 세 가지(커서, 우클릭, 휠)를 짧게. 시연 영상이 있으면 여기서 보여 준다.");
  techBadge(s, "사용 라이브러리", "MediaPipe Hands · OpenCV");
  const cw = 3.7, gap = 0.55, xs = [0.6, 0.6 + cw + gap, 0.6 + 2 * (cw + gap)];
  ["시도", "문제", "해결"].forEach((l, i) => {
    text(s, l, xs[i], 1.85, cw, 0.35, { fontSize: 14, bold: true, color: [MUTED, FAIL, OK][i] });
  });
  const rows = [
    ["커서", "검지 끝을 커서로 사용", "엄지를 붙이는 순간\n검지가 움직여 어긋남", "손바닥 중심으로 변경"],
    ["우클릭", "검지 + 중지 겹치기", "손날 자세에서 오발동", "엄지를 손바닥 중앙으로"],
    ["휠", "중지만 펴서 위아래로", "약지가 같이 움직임.\n거리마다 값이 달라짐", "약지 + 새끼만 말고\n손 전체를 위아래로"],
  ];
  rows.forEach((r, i) => {
    const y = 2.3 + i * 1.55, h = 1.4;
    card(s, xs[0], y, cw, h);
    card(s, xs[1], y, cw, h, FAIL_PALE, false);
    card(s, xs[2], y, cw, h, OK_PALE, false);
    labeled(s, xs[0] + 0.2, y + 0.15, cw - 0.4, h - 0.3, r[0], r[1], INK);
    labeled(s, xs[1] + 0.2, y + 0.15, cw - 0.4, h - 0.3, "원인", r[2], FAIL);
    labeled(s, xs[2] + 0.2, y + 0.15, cw - 0.4, h - 0.3, "변경", r[3], OK);
    [xs[0] + cw, xs[1] + cw].forEach((ax) => text(s, "→", ax, y, gap, h, { fontSize: 24, color: MUTED, align: "center", valign: "middle" }));
  });
  return s;
}

// ── 6. 손: 겹쳐 보이는 문제 (로그로 원인 추적) ──────────
const HANDLOG_CARDS = [
  ["원인", "로그로 확인. 손을 돌리면 2D 화면에서 손가락이 겹쳐 보인다.", FAIL, FAIL_PALE],
  ["해결", "손바닥이 정면일 때만 클릭 판정. 0.1초 이상 유지해야 인정.", OK, OK_PALE],
  ["같은 계열", "거리 영향은 정규화로 제거. 손날 판정은 들어가는 기준과 나오는 기준을 다르게 둬서 깜빡임을 막음.", OK, OK_PALE],
];

function slideHandLog(notes) {
  const s = pres.addSlide();
  header(s, "손");
  s.addNotes(notes || "[0:50 / 누적 5:40] 가장 말할 거리가 많은 장면. 로그를 남겨 확인했더니 손을 돌릴 때 손가락이 겹쳐 보인 것이 원인이었다. 추측한 원인과 실제 원인이 달랐다.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 2.0, w: 4.7, h: 4.6, rectRadius: 0.08, fill: { color: INK }, line: { color: INK, width: 0 } });
  text(s, "엄지–중지 거리", 0.9, 2.3, 4.1, 0.4, { fontSize: 15, color: "C9D0DD" });
  text(s, "0.17 → 0.003", 0.9, 2.95, 4.1, 1.0, { fontSize: 44, bold: true, color: "FFFFFF" });
  text(s, "손을 돌리는 동안 기록된 값", 0.9, 4.15, 4.1, 0.8, { fontSize: 14, color: "C9D0DD" });

  const cards = HANDLOG_CARDS;
  cards.forEach((c, i) => {
    const y = 2.0 + i * 1.57, h = 1.45;
    card(s, 5.6, y, 7.1, h, c[3], false);
    labeled(s, 5.85, y + 0.15, 6.6, h - 0.3, c[0], c[1], c[2]);
  });
  return s;
}

// ── 7. 눈 ───────────────────────────────────────────────
const EYE_CARDS = [
  ["시도", "EAR로 깜빡임 인식, 3초 롱블링크로 모니터 끄기", MUTED, CARD],
  ["문제", "사람마다 눈 크기가 달라 기준값을 따로 맞춰서 진행해도 값 기준이 모호해짐", FAIL, FAIL_PALE],
  ["결정", "이번 기능에서는 제외. 예/아니오는 엄지척 · 엄지다운이 대신 맡음", OK, OK_PALE],
];

function slideEye(notes) {
  const s = pres.addSlide();
  header(s, "눈");
  s.addNotes(notes || "[0:30 / 누적 6:10] 짧게. 넣고 싶었지만 기준값 문제로 이번에는 제외했고 코드는 남겼다.");
  techBadge(s, "사용 라이브러리", "MediaPipe Face Mesh", "눈 비율(EAR)은 직접 계산");
  const cols = EYE_CARDS;
  const w = 3.8, gap = 0.35, x0 = 0.6;
  cols.forEach((c, i) => {
    const x = x0 + i * (w + gap);
    card(s, x, 2.3, w, 3.0, c[3], i === 0);
    labeled(s, x + 0.3, 2.65, w - 0.6, 2.4, c[0], c[1], c[2]);
  });
  return s;
}

// ── 8. LLM ──────────────────────────────────────────────
function slideLLM(notes) {
  const s = pres.addSlide();
  header(s, "LLM");
  s.addNotes(notes || "[0:50 / 누적 7:00] 사용 모델과 이유, 해석이 틀렸던 세 가지와 해결. LLM은 학습하지 않고 매번 지시문과 예시를 다시 읽는다는 점도 한 줄로.");
  card(s, 0.6, 2.0, 4.6, 4.6, INK, false);
  text(s, "사용 모델", 0.9, 2.3, 4.0, 0.4, { fontSize: 15, bold: true, color: "F2B8B2" });
  text(s, "qwen2.5:3b-instruct", 0.9, 2.75, 4.0, 0.9, { fontSize: 20, bold: true, color: "FFFFFF" });
  text(s, "도입 이유", 0.9, 3.9, 4.0, 0.4, { fontSize: 15, bold: true, color: "9ADBC6" });
  text(s, "코드 수정 없이 제스처에 원하는 명령을 연결해 보고 싶어서. 인식은 코드가, 문장 해석은 LLM이 맡는다.", 0.9, 4.35, 4.0, 2.0, { fontSize: 15, color: "C9D0DD" });

  const rows = [
    ["\"음소거\"를\n모니터 끄기로 해석", "예시를 프롬프트에 추가\n(7문장 모두 정답)"],
    ["없는 동작을\n만들어 냄", "허용 목록만 실행\n예시로 교정"],
    ["응답 지연 예외로\n프로그램 전체 종료", "그 명령만 실패 처리\n모델은 메모리에 유지"],
  ];
  rows.forEach((r, i) => {
    const y = 2.0 + i * 1.57, h = 1.45;
    card(s, 5.5, y, 3.5, h, FAIL_PALE, false);
    card(s, 9.3, y, 3.4, h, OK_PALE, false);
    text(s, r[0], 5.7, y + 0.15, 3.1, h - 0.3, { fontSize: 16 });
    text(s, r[1], 9.5, y + 0.15, 3.0, h - 0.3, { fontSize: 16 });
    text(s, "→", 9.0, y, 0.3, h, { fontSize: 20, color: MUTED, align: "center", valign: "middle" });
  });
  return s;
}

// 카드 4장 + 아래 현재 상태 띠 (음성 · 포즈 · 박수 공통)
function fourCards(s, cards, noteLabel, noteBody) {
  const gap = 0.23, x0 = 0.6, w = (12.1 - gap * (cards.length - 1)) / cards.length;
  cards.forEach((c, i) => {
    const x = x0 + i * (w + gap);
    card(s, x, 2.0, w, 2.9, c[3], c[3] === CARD);
    labeled(s, x + 0.2, 2.2, w - 0.4, 2.5, c[0], c[1], c[2], 21, 19);
  });
  card(s, 0.6, 5.2, 12.1, 1.3, HOLD_PALE, false);
  text(s, [
    { text: noteLabel, options: { bold: true, color: HOLD } },
    { text: noteBody, options: { color: INK } },
  ], 0.9, 5.4, 11.5, 0.9, { fontSize: 18 });
}

// ── 9. 음성 ─────────────────────────────────────────────
const VOICE_CARDS = [
  ["모델", "소음을 고려해 small보다 큰 모델 선택", INK, CARD],
  ["① 손등 3초", "손을 떼면 녹음 종료. 소음 환경의 주력", INK, CARD],
  ["② 웨이크워드", "무음 1.2초 뒤 자동 종료. \"웨이크\"는 임시값", INK, CARD],
  ["역할 분리", "Whisper는 받아쓰기만. 해석은 LLM이", OK, OK_PALE],
];
const VOICE_NOTE = "음성 인식이 궁금해서 넣었다. 소음이 크지 않은 곳에서는 잘 인식한다.";

function slideVoice(notes) {
  const s = pres.addSlide();
  header(s, "음성");
  s.addNotes(notes || "[0:40 / 누적 7:40] 두 가지 트리거(손등 3초, 웨이크워드)와 역할 분리. 조용한 환경에서는 잘 인식했다.");
  techBadge(s, "사용 모델", "faster-whisper medium");
  fourCards(s, VOICE_CARDS, "계기: ", VOICE_NOTE);
  return s;
}

// ── 10. 포즈 ────────────────────────────────────────────
function slidePose(notes) {
  const s = pres.addSlide();
  header(s, "포즈");
  s.addNotes(notes || "[0:40 / 누적 8:20] 라이브러리 선택 이유, 22차원 특징, 지금 단계(특징 추출까지)와 다음 단계.");
  fourCards(s, [
    ["라이브러리", "MediaPipe Pose. 설치돼 있고 가시성 정보를 준다", INK, CARD],
    ["22차원 특징", "좌표 18 + 팔꿈치 각도 2 + 머리 방향 2", INK, CARD],
    ["모드 분리", "한 번에 하나만 켜서 충돌 방지. 명령 모듈은 공유", OK, OK_PALE],
  ], "계기: ", "포즈 인식 참고 예제(YOLO)를 보고 넣어 보고 싶었다. 지금은 특징 추출까지, 자세 등록과 인식은 다음 단계.");
  return s;
}

// ── 11. 박수 ────────────────────────────────────────────
const CLAP_CARDS = [
  ["가정", "소리 감지가 약해서 인식이 안 된다", MUTED, CARD],
  ["로그 확인", "신호는 이미 정상으로 잡히고 있었다", INK, CARD],
  ["진짜 원인", "박수 신호(30ms)와 카메라 프레임(33ms)이 잘 안 겹침. 양손이 하나로 검출되기도 함", FAIL, FAIL_PALE],
  ["해결", "직전 1초 안에 양손이 모였으면 인정", OK, OK_PALE],
];
const CLAP_NOTE = "양손 모으기 1초로 모드를 전환. 키보드 소리와 박수는 음량(peak)으로 구분.";

function slideClap(notes) {
  const s = pres.addSlide();
  header(s, "박수");
  s.addNotes(notes || "[0:40 / 누적 9:00] 인식이 안 된다고 생각했지만 로그를 보니 신호는 잡히고 있었다. 타이밍이 원인이었고, 결국 양손 모으기로 전환.");
  techBadge(s, "사용 라이브러리", "sounddevice · NumPy", "별도 모델 없이 음량 변화로 감지");
  fourCards(s, CLAP_CARDS, "결국: ", CLAP_NOTE);
  return s;
}

// ── 12. 교훈 ────────────────────────────────────────────
function slideLessons(notes) {
  const s = pres.addSlide();
  header(s, "교훈");
  s.addNotes(notes || "[0:50 / 누적 9:50] 네 가지 교훈으로 마무리. 로그로 확인하는 습관이 가장 크게 남았다.");
  const L = [
    ["고정 좌표 대신 비율", "어깨 너비 등으로 나눠야 거리에 안 흔들림"],
    ["순간과 유지를 구분", "전환 자세는 최소 유지시간으로 걸러냄"],
    ["추측 말고 로그", "두 번 모두 짐작한 원인과 실제 원인이 달랐다"],
    ["2D 화면의 한계", "돌리면 떨어져 있어도 겹쳐 보임"],
  ];
  // 4장이면 2열(2x2), 그 외에는 3열. 마지막 줄이 모자라면 가운데 정렬.
  const cols = L.length <= 4 ? 2 : 3;
  const h = 2.1, gx = 0.35, gy = 0.35, x0 = 0.6, y0 = 2.0, w = (12.1 - gx * (cols - 1)) / cols;
  L.forEach((l, i) => {
    const row = Math.floor(i / cols), inRow = i % cols, rowCount = Math.min(cols, L.length - row * cols);
    const x = x0 + ((cols - rowCount) * (w + gx)) / 2 + inRow * (w + gx), y = y0 + row * (h + gy);
    card(s, x, y, w, h);
    text(s, String(i + 1), x + 0.25, y + 0.2, 0.6, 0.6, { fontSize: 28, bold: true, color: OK });
    labeled(s, x + 0.25, y + 0.85, w - 0.5, h - 1.0, l[0], l[1], INK);
  });
  return s;
}


// ══════════════════════════════════════════════════════════
//  과정 중심 덱: 문제 정의 → 기존 방법 · 한계 → 방안과 이유 → 설계 → 구현에서 이해한 것 → 검증
//  (기존 덱은 그대로 두고, 위의 슬라이드 함수를 재사용하면서 아래 새 슬라이드를 더한다)
// ══════════════════════════════════════════════════════════

const tHead = (labels) => labels.map((t) => ({
  text: t, options: { bold: true, color: "FFFFFF", fill: { color: INK }, fontSize: 14 },
}));
const tLink = (label, url) => ({ text: label, options: { fontSize: 12, hyperlink: { url } } });
const tPlain = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: INK }, o) });
const tableOpts = (colW, rowH) => ({
  x: 0.6, y: 1.95, w: 12.1, colW, rowH, fontFace: FONT, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1],
  border: { type: "solid", pt: 0.75, color: "DDE0E6" }, fill: { color: CARD },
});

// 불릿 목록이 들어가는 카드 (제목 + 항목들)
function bulletCard(s, x, y, w, h, fill, shadowOn, title, titleColor, items, size = 15, gap = 8) {
  card(s, x, y, w, h, fill, shadowOn);
  const runs = [{ text: title, options: { fontSize: 19, bold: true, color: titleColor, breakLine: true } }];
  items.forEach((t, i) => {
    runs.push({ text: t, options: { fontSize: size, color: INK, bullet: true, paraSpaceBefore: gap, breakLine: i < items.length - 1 } });
  });
  text(s, runs, x + 0.3, y + 0.25, w - 0.6, h - 0.5, {});
}

// 2. 문제 정의
function pSlideProblem(notes) {
  const s = pres.addSlide();
  header(s, "문제 정의");
  s.addNotes(notes);
  const stages = [
    ["출발", "수어 인식 프로젝트에서 MediaPipe 손 인식을 써 봄", MUTED, CARD],
    ["질문", "이 손 인식을 어디에 더 쓸 수 있을까", INK, CARD],
    ["문제", "동작이 정해져 있으면 사용자가 원하는 대로 쓸 수 없다", FAIL, FAIL_PALE],
    ["목표", "클릭 · 예/아니오를 뺀 모든 동작을 사용자가 직접 정의", OK, OK_PALE],
  ];
  const gap = 0.5, w = (12.1 - gap * 3) / 4;
  stages.forEach((st, i) => {
    const x = 0.6 + i * (w + gap);
    card(s, x, 2.2, w, 3.4, st[3], st[3] === CARD);
    labeled(s, x + 0.2, 2.45, w - 0.4, 2.9, st[0], st[1], st[2], 24, 21);
    if (i < 3) text(s, "→", x + w, 2.2, gap, 3.4, { fontSize: 24, color: MUTED, align: "center", valign: "middle" });
  });
  return s;
}

// 3. 기존 방법과 한계 (발표 준비 중 공개 자료로 확인한 내용)
function pSlideExisting(notes) {
  const s = pres.addSlide();
  header(s, "기존 방법과 한계");
  s.addNotes(notes);
  const rows = [
    ["Project Gameface", "얼굴 움직임으로 마우스 조작\n(접근성)", "손이 아닌 얼굴 입력. 표정에 동작을 연결하는 설정 방식", tLink("blog.google", "https://blog.google/technology/ai/google-project-gameface/")],
    ["Talon Voice", "음성으로 PC 제어", "명령을 스크립트(.talon)로 직접 정의", tLink("talonvoice.com/docs", "https://talonvoice.com/docs/")],
    ["Open Interpreter", "LLM이 PC에서 코드를 실행", "임의 코드 실행. 안전은 실행 전 확인에 의존", tLink("docs.openinterpreter.com", "https://docs.openinterpreter.com/safety/introduction")],
    ["Home Assistant + Ollama", "Whisper와 로컬 LLM으로\n집 기기 제어", "구조는 비슷, 대상은 PC가 아닌 집 기기", tLink("home-assistant.io", "https://www.home-assistant.io/integrations/ollama")],
  ].map((r) => r.map((c, i) => (typeof c === "string" ? tPlain(c, i === 0 ? { bold: true } : {}) : c)));
  s.addTable([tHead(["방법", "하는 일", "우리 목표와 다른 점", "출처"]), ...rows], tableOpts([2.4, 3.0, 4.2, 2.5], [0.5, 0.9, 0.9, 0.9, 0.9]));
  text(s, "직접 써 본 것이 아니라 공개 자료로 확인한 내용이다 (발표 준비 중 조사).", 0.6, 6.4, 12.1, 0.4, { fontSize: 14, color: MUTED });
  return s;
}

// 4. 방안과 이유
function pSlidePlan(notes) {
  const s = pres.addSlide();
  header(s, "방안과 이유");
  s.addNotes(notes);
  const cw = 3.7, gap = 0.55, xs = [0.6, 0.6 + cw + gap, 0.6 + 2 * (cw + gap)];
  ["아쉬운 점", "방안", "이유"].forEach((l, i) => {
    text(s, l, xs[i], 1.75, cw, 0.35, { fontSize: 14, bold: true, color: [FAIL, MUTED, OK][i] });
  });
  const rows = [
    ["명령을 코드로 정의해야 한다 (Talon)", "자연어로 명령을 등록한다", "코드 없이 동작을 붙이려고"],
    ["임의 코드를 실행한다 (Open Interpreter)", "허용 목록의 동작만 실행한다", "틀려도 위험한 동작은 막으려고"],
    ["입력마다 도구가 따로 있다\n(얼굴, 음성)", "손 · 포즈 · 음성이\n명령 엔진 하나를 공유한다", "입력을 늘려도 명령은\n한곳에서 관리하려고"],
    ["집 기기 중심이다 (Home Assistant)", "PC 동작에 맞춘 목록, 로컬 실행", "데이터가 PC 밖으로\n나가지 않게"],
  ];
  rows.forEach((r, i) => {
    const y = 2.2 + i * 1.12, h = 1.0;
    card(s, xs[0], y, cw, h, FAIL_PALE, false);
    card(s, xs[1], y, cw, h);
    card(s, xs[2], y, cw, h, OK_PALE, false);
    r.forEach((t, j) => text(s, t, xs[j] + 0.2, y, cw - 0.4, h, { fontSize: 16, valign: "middle" }));
    [xs[0] + cw, xs[1] + cw].forEach((ax) => text(s, "→", ax, y, gap, h, { fontSize: 24, color: MUTED, align: "center", valign: "middle" }));
  });
  return s;
}

// 6. 도구와 선택 이유
function pSlideToolsWhy(notes) {
  const s = pres.addSlide();
  header(s, "도구와 선택 이유");
  s.addNotes(notes);
  const same = tPlain("위와 동일", { color: MUTED, fontSize: 12 });
  const rows = [
    ["손", "MediaPipe Hands · OpenCV", "수어 프로젝트에서 써 본 MediaPipe", tLink("github.com/google-ai-edge/mediapipe", "https://github.com/google-ai-edge/mediapipe")],
    ["눈", "MediaPipe Face Mesh", "같은 MediaPipe로 눈 감김 비율(EAR) 계산", same],
    ["포즈", "MediaPipe Pose", "이미 쓰던 MediaPipe, 가시성 정보 제공", same],
    ["음성", "faster-whisper medium", "소음을 고려해 small보다 큰 모델", tLink("huggingface.co/Systran/faster-whisper-medium", "https://huggingface.co/Systran/faster-whisper-medium")],
    ["LLM", "Qwen2.5-3B-Instruct (Ollama)", "작은 모델을 로컬에서 실행", tLink("huggingface.co/Qwen/Qwen2.5-3B-Instruct", "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct")],
    ["박수", "sounddevice · NumPy", "모델 없이 음량 변화로 간단히 감지", tPlain("—", { color: MUTED })],
    ["PC 제어", "pywin32", "Windows 마우스 · 키보드 · 창을 직접 제어", tLink("github.com/mhammond/pywin32", "https://github.com/mhammond/pywin32")],
  ].map((r) => r.map((c, i) => (typeof c === "string" ? tPlain(c, i === 0 ? { bold: true } : {}) : c)));
  s.addTable([tHead(["영역", "도구 · 모델", "왜 썼나", "출처"]), ...rows], tableOpts([1.1, 2.9, 4.0, 4.1], 0.56));
  return s;
}

// 12. 검증과 한계
function pSlideVerify(notes) {
  const s = pres.addSlide();
  header(s, "검증과 한계");
  s.addNotes(notes);
  const cols = [
    ["확인한 방법", INK, CARD, true, ["판정값을 로그로 남겨 원인 확인 (손, 박수)", "녹음 5개를 받아쓰기 → 해석", "예시 문장으로 LLM 해석 확인"]],
    ["확인 결과", OK, OK_PALE, false, ["음성: 받아쓰기 5개 중 4개 정확, 해석은 5개 모두 의도대로", "LLM: 예시 7문장 모두 정답", "손: 겹침 오발동 해결"]],
    ["한계", FAIL, FAIL_PALE, false, ["표본이 작다 (파일 5개, 조용한 환경)", "소음 환경은 확인하지 못했다", "포즈는 특징 추출까지, 박수는 전환에서 제외"]],
  ];
  const w = 3.8, gap = 0.35;
  cols.forEach((c, i) => bulletCard(s, 0.6 + i * (w + gap), 2.0, w, 3.5, c[2], c[3], c[0], c[1], c[4], 16));
  card(s, 0.6, 5.8, 12.1, 0.85, HOLD_PALE, false);
  text(s, [
    { text: "개발 방식: ", options: { bold: true, color: HOLD } },
    { text: "Claude Code를 코드 작성 · 설계 조언 · 원인 분석에 활용했다. 제품 안의 Qwen과는 별개다.", options: { color: INK } },
  ], 0.9, 5.8, 11.5, 0.85, { fontSize: 15, valign: "middle" });
  return s;
}

// 13. 정리 (알게 된 것 + 다음 단계)
function pSlideSummary(notes) {
  const s = pres.addSlide();
  header(s, "정리");
  s.addNotes(notes);
  bulletCard(s, 0.6, 2.0, 7.0, 4.3, CARD, true, "알게 된 것", OK, [
    "LLM은 학습하지 않고 매번 지시문을 다시 읽는다",
    "로컬 LLM은 대화만 하니 코드로 연결해야 한다",
    "손을 돌리면 2D 화면에서 손가락이 겹쳐 보인다",
    "추측하지 말고 로그로 확인한다",
  ], 19, 18);
  bulletCard(s, 8.0, 2.0, 4.7, 4.3, HOLD_PALE, false, "다음 단계", HOLD, [
    "자세 등록 · 인식",
    "UI 통합",
    "웨이크워드 확정",
  ], 21, 18);
  return s;
}

// ── 과정 중심 덱 전용: 왼쪽 패널(사용 모델/라이브러리 + 이유) + 오른쪽 내용 ──
// LLM 슬라이드와 같은 배치로 맞춘다. 기존 덱의 슬라이드(오른쪽 위 작은 상자)는 그대로 둔다.

// 왼쪽 어두운 패널 (LLM 슬라이드의 패널과 같은 위치 · 크기 · 색)
function techPanel(s, label, name, reason) {
  card(s, 0.6, 2.0, 4.6, 4.6, INK, false);
  text(s, label, 0.9, 2.3, 4.0, 0.4, { fontSize: 15, bold: true, color: "F2B8B2" });
  text(s, name, 0.9, 2.75, 4.0, 0.9, { fontSize: 20, bold: true, color: "FFFFFF" });
  text(s, "도입 이유", 0.9, 3.9, 4.0, 0.4, { fontSize: 15, bold: true, color: "9ADBC6" });
  text(s, reason, 0.9, 4.35, 4.0, 2.0, { fontSize: 15, color: "C9D0DD" });
}

const PANEL_X = 5.5, PANEL_W = 7.2; // 패널 오른쪽 내용 영역

// 손: 라이브러리는 패널로, 오른쪽에는 원인 · 해결 (로그 수치 0.17 → 0.003은 슬라이드에 없고 발표자 노트에 있다)
function pSlideHandPanel(notes) {
  const s = pres.addSlide();
  header(s, "손");
  s.addNotes(notes);
  techPanel(s, "사용 라이브러리", "MediaPipe Hands · OpenCV", "수어 인식 프로젝트에서 써 본\nMediaPipe를 이어서 사용.");
  HANDLOG_CARDS.forEach((c, i) => {
    const y = 2.0 + i * 1.55;
    card(s, PANEL_X, y, PANEL_W, 1.4, c[3], false);
    labeled(s, PANEL_X + 0.25, y + 0.15, PANEL_W - 0.5, 1.1, c[0], c[1], c[2], 18, 15);
  });
  return s;
}

// 음성: 모델은 패널로, 오른쪽에는 트리거 두 가지와 역할 분리
function pSlideVoicePanel(notes) {
  const s = pres.addSlide();
  header(s, "음성");
  s.addNotes(notes);
  techPanel(s, "사용 모델", "faster-whisper medium", "음성 인식이 궁금해서. 소음을 고려해 small보다 큰 모델을 선택.");
  VOICE_CARDS.slice(1).forEach((c, i) => {
    const y = 2.0 + i * 1.1;
    card(s, PANEL_X, y, PANEL_W, 1.0, c[3], c[3] === CARD);
    labeled(s, PANEL_X + 0.25, y + 0.1, PANEL_W - 0.5, 0.8, c[0], c[1], c[2], 17, 16);
  });
  card(s, PANEL_X, 5.4, PANEL_W, 1.2, HOLD_PALE, false);
  text(s, [
    { text: "확인: ", options: { bold: true, color: HOLD } },
    { text: "소음이 크지 않은 곳에서는 잘 인식한다 (녹음 5개 기준)", options: { color: INK } },
  ], PANEL_X + 0.25, 5.4, PANEL_W - 0.5, 1.2, { fontSize: 16, valign: "middle" });
  return s;
}

// 눈: 라이브러리는 패널로, 오른쪽에는 시도 · 문제 · 결정을 세로로
function pSlideEyePanel(notes) {
  const s = pres.addSlide();
  header(s, "눈");
  s.addNotes(notes);
  techPanel(s, "사용 라이브러리", "MediaPipe Face Mesh", "같은 MediaPipe로 눈 감김 비율(EAR) 계산.");
  EYE_CARDS.forEach((c, i) => {
    const y = 2.0 + i * 1.55;
    card(s, PANEL_X, y, PANEL_W, 1.4, c[3], c[3] === CARD);
    labeled(s, PANEL_X + 0.25, y + 0.15, PANEL_W - 0.5, 1.1, c[0], c[1], c[2], 18, 16);
  });
  return s;
}

// 박수: 라이브러리는 패널로, 오른쪽에는 네 단계를 2x2로 + 결론 띠
function pSlideClapPanel(notes) {
  const s = pres.addSlide();
  header(s, "박수");
  s.addNotes(notes);
  techPanel(s, "사용 라이브러리", "sounddevice · NumPy", "별도 모델 없이 음량 변화로 간단히 감지.");
  const gap = 0.2, w = (PANEL_W - gap) / 2;
  CLAP_CARDS.forEach((c, i) => {
    const x = PANEL_X + (i % 2) * (w + gap), y = 2.0 + Math.floor(i / 2) * 1.55;
    card(s, x, y, w, 1.45, c[3], c[3] === CARD);
    labeled(s, x + 0.15, y + 0.12, w - 0.25, 1.2, c[0], c[1], c[2], 16, 14);
  });
  card(s, PANEL_X, 5.2, PANEL_W, 1.4, HOLD_PALE, false);
  text(s, [
    { text: "결국: ", options: { bold: true, color: HOLD } },
    { text: CLAP_NOTE, options: { color: INK } },
  ], PANEL_X + 0.25, 5.2, PANEL_W - 0.5, 1.4, { fontSize: 16, valign: "middle" });
  return s;
}

// ── 덱 빌드 ─────────────────────────────────────────────

// 기존 덱: 시행착오로 보는 개발 과정 (13장)
function buildDevlog() {
  newDeck("개인 AI 비서 — 시행착오로 보는 개발 과정");
  slideCover();
  slidePurpose();
  slideFlow();
  slideTools();
  slideDevMethod();
  slideHand();
  slideHandLog();
  slideEye();
  slideLLM();
  slideVoice();
  slidePose();
  slideClap();
  slideLessons();
  return pres.writeFile({ fileName: "assistant_devlog.pptx" });
}

// 과정 중심 덱: 문제 정의에서 검증까지 (13장, 약 9분 50초)
function buildProcess() {
  newDeck("개인 AI 비서 — 문제에서 검증까지, 선택한 이유");
  slideCover("문제에서 검증까지, 선택한 이유", "[0:20 / 누적 0:20] 인사와 한 줄 소개. 이번 발표는 구현한 것보다 과정에서 이해한 것과 선택한 이유 중심. 약 10분.");
  pSlideProblem("[0:50 / 누적 1:10] 수어 인식 프로젝트에서 MediaPipe 손 인식을 써 본 뒤, 이걸 어디에 더 쓸 수 있을까 고민했다. 동작이 정해져 있으면 사용자가 원하는 대로 못 쓴다는 점을 문제로 잡았고, 목표는 클릭과 예/아니오를 뺀 모든 동작을 사용자가 정의하는 것.");
  pSlideExisting("[1:00 / 누적 2:10] 발표를 준비하며 공개 자료로 기존 방법을 확인했다. 직접 써 본 것은 아니라는 점을 먼저 밝힌다. 각각 목적이 달라서 우리 목표와 다른 점을 짚는다.");
  pSlidePlan("[0:50 / 누적 3:00] 확인한 아쉬운 점마다 방안과 이유를 짝지어 말한다. 자연어 등록, 허용 목록, 명령 엔진 공유, 로컬 실행.");
  slideFlow("[0:50 / 누적 3:50] 설계. 입력에서 출력까지 한 줄로. 인식 모듈은 동작의 이름만 넘기고 실행은 다른 곳이 맡는다.");
  pSlideToolsWhy("[0:50 / 누적 4:40] 도구마다 왜 썼는지. 손은 수어 프로젝트에서 써 본 MediaPipe를 이어서 썼다. 모델은 출처 링크를 붙였다.");
  pSlideHandPanel("[0:50 / 누적 5:30] 구현하며 이해한 것 1. 클릭이 계속 발동해서 로그를 남겨 확인했다. 손을 정면에서 옆으로, 뒤로 돌리는 동안 엄지–중지 거리가 0.17에서 0.003까지 떨어졌다. 실제로 붙인 게 아니라 2D 화면에서 손가락이 겹쳐 보인 것이었다. 추측한 원인과 실제 원인이 달랐다.");
  slideLLM("[0:50 / 누적 6:20] 구현하며 이해한 것 2. 로컬 LLM은 학습하지 않고 매번 지시문과 예시를 다시 읽는다. 해석이 틀린 세 가지와 해결.");
  pSlideVoicePanel("[0:40 / 누적 7:00] 구현하며 이해한 것 3. 두 가지 트리거와 역할 분리. 조용한 환경에서는 잘 인식했다.");
  pSlideEyePanel("[0:25 / 누적 7:25] 넣고 싶었지만 기준값 문제로 이번에는 제외했다.");
  pSlideClapPanel("[0:35 / 누적 8:00] 인식이 안 된다고 생각했지만 로그를 보니 신호는 잡히고 있었다. 타이밍이 원인.");
  pSlideVerify("[1:00 / 누적 9:00] 어떻게 확인했고 무엇을 확인하지 못했는지. 표본이 작고 소음 환경은 못 봤다는 점을 분명히. 개발에는 Claude Code를 썼다.");
  pSlideSummary("[0:50 / 누적 9:50] 알게 된 것으로 마무리하고 다음 단계를 말한다.");
  return pres.writeFile({ fileName: "assistant_process.pptx" });
}

// node build.js            → 기존 덱(assistant_devlog.pptx)만
// node build.js process    → 과정 중심 덱(assistant_process.pptx)만
// node build.js all        → 둘 다
(async () => {
  const which = process.argv[2] || "devlog";
  if (which === "devlog" || which === "all") console.log("saved:", await buildDevlog());
  if (which === "process" || which === "all") console.log("saved:", await buildProcess());
})();
