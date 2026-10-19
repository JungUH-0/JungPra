// 개인 AI 비서 — 시행착오로 보는 개발 과정 (발표용)
// 소스는 이 파일, .pptx는 산출물. 내용 근거는 ../DEVLOG.md
// v7 = v2 기반, 12장(다음 단계 삭제, 교훈 4개, 포즈 카드 3개): 목차 · 흐름 · 음성 · 포즈 추가, 영역 태그 제거)에 맞춰 갱신됨.
//   npm install pptxgenjs
//   node build.js
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "개인 AI 비서";
pres.title = "개인 AI 비서 — 시행착오로 보는 개발 과정";

// ── palette ─────────────────────────────────────────────
const INK = "1B2230";        // 지배색 (어두운 남색)
const PAPER = "F5F6F8";
const CARD = "FFFFFF";
const MUTED = "6A7384";
const PAGE = "8F8F8F";       // 목차 쪽수
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

// 라벨 + 본문 (카드 안 텍스트)
function labeled(slide, x, y, w, h, label, body, labelColor, ls = 17, bs = 16) {
  text(slide, [
    { text: label, options: { fontSize: ls, bold: true, color: labelColor, breakLine: true } },
    { text: body, options: { fontSize: bs, color: INK } },
  ], x, y, w, h, { paraSpaceAfter: 4 });
}

// 목차 · 흐름 공통: 번호 칸 + 흰 카드(굵은 제목 + 설명). pageText가 있으면 오른쪽에 쪽수.
function listRows(slide, rows, hasPage) {
  const y0 = 1.94, step = 0.833, h = 0.72;
  rows.forEach((r, i) => {
    const y = y0 + i * step;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.6, y, w: 0.97, h, rectRadius: 0.08, fill: { color: INK }, line: { color: INK, width: 0 },
    });
    text(slide, String(i + 1).padStart(2, "0"), 0.6, y, 0.97, h, { fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    card(slide, 1.74, y, 10.96, h);
    text(slide, [
      { text: r.label, options: { bold: true, color: INK } },
      { text: "   " + r.desc, options: { color: INK } },
    ], 1.99, y, hasPage ? 9.4 : 10.5, h, { fontSize: 15, valign: "middle" });
    if (hasPage) text(slide, r.page, 10.97, y, 1.53, h, { fontSize: 14, color: PAGE, align: "right", valign: "middle" });
  });
}

// ── 1. 표지 ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: INK };
  text(s, "개인 AI 비서", 0.9, 2.2, 11.5, 1.0, { fontSize: 54, bold: true, color: "FFFFFF" });
  text(s, "시행착오로 보는 개발 과정", 0.9, 3.35, 11.5, 0.7, { fontSize: 30, color: "C9D0DD" });
  text(s, "손동작 · 음성 · 포즈를 로컬 LLM으로 해석해서 PC를 제어한다", 0.9, 4.5, 11.5, 0.5, { fontSize: 18, color: "9AA4B6" });
}

// ── 2. 목차 ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "목차");
  listRows(s, [
    { label: "개요 · 흐름", desc: "만든 것의 전체 모습과 커밋으로 본 다섯 번의 전환점", page: "p.3 ~ 4" },
    { label: "손", desc: "커서 · 우클릭 · 휠, 그리고 손가락이 겹쳐 보인 문제", page: "p.5 ~ 6" },
    { label: "눈", desc: "눈 기능을 이번에는 제외한 이유", page: "p.7" },
    { label: "LLM · 음성", desc: "사용한 모델과 도입 이유, 두 가지 음성 트리거", page: "p.8 ~ 9" },
    { label: "포즈 · 박수", desc: "22차원 특징 추출, 박수를 접고 양손 모으기", page: "p.10 ~ 11" },
    { label: "교훈", desc: "반복된 실수 네 가지", page: "p.12" },
  ], true);
}

// ── 3. 개요 ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "개요");
  const items = [
    { name: "손", sub: "커서 · 클릭 · 휠\n예 / 아니오", st: "완성", c: OK, p: OK_PALE },
    { name: "눈", sub: "깜빡임 · 롱블링크", st: "제외", c: HOLD, p: HOLD_PALE },
    { name: "LLM · 음성", sub: "명령 해석 · 음성 입력", st: "구현", c: OK, p: OK_PALE },
    { name: "포즈", sub: "상체 22차원 특징 추출", st: "등록 예정", c: HOLD, p: HOLD_PALE },
    { name: "박수", sub: "모드 전환 신호", st: "전환에서 제외", c: HOLD, p: HOLD_PALE },
  ];
  const w = 2.31, gap = 0.2, x0 = 0.49, y = 2.5, h = 3.3;
  items.forEach((it, i) => {
    const x = x0 + i * (w + gap);
    card(s, x, y, w, h);
    text(s, it.name, x + 0.22, y + 0.3, 1.92, 0.7, { fontSize: 26, bold: true });
    text(s, it.sub, x + 0.22, y + 1.15, 1.92, 1.0, { fontSize: 15, color: MUTED });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.22, y: y + h - 0.85, w: 1.86, h: 0.5, rectRadius: 0.25, fill: { color: it.p }, line: { color: it.p, width: 0 },
    });
    text(s, it.st, x + 0.22, y + h - 0.85, 1.86, 0.5, { fontSize: 13, bold: true, color: it.c, align: "center", valign: "middle" });
  });
}

// ── 4. 흐름 (커밋으로 본 전환점) ────────────────────────
{
  const s = pres.addSlide();
  header(s, "흐름");
  listRows(s, [
    { label: "첫 시도", desc: "수어 인식 프로젝트의 MediaPipe 손 인식에서 출발. 추가 활용법을 찾다가 비서로 발전" },
    { label: "로컬 LLM 도입", desc: "Ollama 기반 명령 등록 모듈을 만들고 main.py에 연결" },
    { label: "손 안정화", desc: "오발동을 잡고 LLM이 해석하는 명령 종류를 확장" },
    { label: "음성 명령", desc: "웨이크워드와 손등 트리거로 녹음해 바로 실행" },
    { label: "포즈 · 모드 전환", desc: "전신 포즈 모드를 더하고, 손과 포즈를 전환. 안정성도 개선" },
  ], false);
}

// ── 5. 손: 커서 · 우클릭 · 휠 ───────────────────────────
{
  const s = pres.addSlide();
  header(s, "손");
  const cw = 3.7, gap = 0.55, xs = [0.6, 0.6 + cw + gap, 0.6 + 2 * (cw + gap)];
  ["시도", "문제", "해결"].forEach((l, i) => {
    text(s, l, xs[i], 1.85, cw, 0.35, { fontSize: 14, bold: true, color: [MUTED, FAIL, OK][i] });
  });
  const rows = [
    ["커서", "검지 끝을 커서로 사용", "클릭하려고 엄지를 붙이는 순간 검지가 움직여 커서가 어긋남", "손바닥 중심(손목 + 관절 평균)으로 변경. 핀치와 무관하게 안정"],
    ["우클릭", "검지 + 중지 겹치기", "손날 자세에서 손가락이 붙어 우클릭이 오발동", "엄지를 손바닥 중앙으로 넣는 동작으로 교체"],
    ["휠", "중지만 펴서 위아래로, 이후 고정 거리 기준", "약지가 중지와 같이 움직임. 카메라 거리마다 값이 달라짐", "약지 + 새끼만 말고 손 전체를 위아래로 (검증된 방식 재사용)"],
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
}

// ── 6. 손: 겹쳐 보이는 문제 (로그로 원인 추적) ──────────
{
  const s = pres.addSlide();
  header(s, "손");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 2.0, w: 4.7, h: 4.6, rectRadius: 0.08, fill: { color: INK }, line: { color: INK, width: 0 } });
  text(s, "엄지–중지 거리", 0.9, 2.3, 4.1, 0.4, { fontSize: 15, color: "C9D0DD" });
  text(s, "0.17 → 0.003", 0.9, 2.95, 4.1, 1.0, { fontSize: 44, bold: true, color: "FFFFFF" });
  text(s, "손을 정면에서 옆으로, 뒤로 돌리는 동안 기록된 값", 0.9, 4.15, 4.1, 0.8, { fontSize: 14, color: "C9D0DD" });

  const cards = [
    ["원인", "추측하지 않고 매 프레임 판정값을 파일로 남겨 확인. 손을 돌리면 카메라 2D 화면에서 손가락이 겹쳐 보인다.", FAIL, FAIL_PALE],
    ["해결", "클릭류 제스처는 손이 정면(손바닥)일 때만 판정. ON/OFF 이중 임계값과 0.1초 유지시간을 추가.", OK, OK_PALE],
    ["같은 계열", "손날 오인식: 거리에 따라 값이 변해서 단위벡터로 정규화. 판정 깜빡임: 0.28 미만에서 손날로 진입, 0.42 초과에서 해제. 그 사이는 직전 상태 유지.", OK, OK_PALE],
  ];
  cards.forEach((c, i) => {
    const y = 2.0 + i * 1.57, h = 1.45;
    card(s, 5.6, y, 7.1, h, c[3], false);
    labeled(s, 5.85, y + 0.15, 6.6, h - 0.3, c[0], c[1], c[2]);
  });
}

// ── 7. 눈 ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "눈");
  const cols = [
    ["시도", "EAR로 깜빡임을 인식하고, 3초 롱블링크로 모니터 끄기까지 연결", MUTED, CARD],
    ["문제", "사람마다 눈 크기가 달라 기준값을 따로 맞춰야 함. 수치 조정에만 시간이 들어가는 중이었다", FAIL, FAIL_PALE],
    ["결정", "눈 기능은 넣고 싶었지만 어려움이 있어 이번 기능에서는 제외했다. 예/아니오는 엄지척 · 엄지다운이 대신 맡음", OK, OK_PALE],
  ];
  const w = 3.8, gap = 0.35, x0 = 0.6;
  cols.forEach((c, i) => {
    const x = x0 + i * (w + gap);
    card(s, x, 2.3, w, 3.0, c[3], i === 0);
    labeled(s, x + 0.3, 2.65, w - 0.6, 2.4, c[0], c[1], c[2]);
  });
}

// ── 8. LLM ──────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "LLM");
  card(s, 0.6, 2.0, 4.6, 4.6, INK, false);
  text(s, "사용 모델", 0.9, 2.3, 4.0, 0.4, { fontSize: 15, bold: true, color: "F2B8B2" });
  text(s, "qwen2.5:3b-instruct", 0.9, 2.75, 4.0, 0.9, { fontSize: 20, bold: true, color: "FFFFFF" });
  text(s, "도입 이유", 0.9, 3.9, 4.0, 0.4, { fontSize: 15, bold: true, color: "9ADBC6" });
  text(s, "제스처에 원하는 명령을 코드 수정 없이 연결해 보고 싶어서 넣었다. 실시간 인식은 코드가, 문장 해석은 LLM이 맡도록 나눴다. Ollama로 로컬에서 실행한다.", 0.9, 4.35, 4.0, 2.0, { fontSize: 15, color: "C9D0DD" });

  const rows = [
    ["\"음소거\"가 모니터 끄기로 해석됨", "대비 예시를 프롬프트에 추가 (테스트 7/7 정답)"],
    ["\"탭 닫아줘\"에서 없는 동작을 만들어 냄", "허용 목록에 있는 동작만 실행, 프롬프트에 예시로 교정"],
    ["응답이 늦어 예외가 메인 루프까지 올라와 프로그램이 통째로 종료", "예외는 그 명령만 실패시키고, 음성 명령은 별도 스레드, 모델은 30분 메모리 유지"],
  ];
  rows.forEach((r, i) => {
    const y = 2.0 + i * 1.57, h = 1.45;
    card(s, 5.5, y, 3.5, h, FAIL_PALE, false);
    card(s, 9.3, y, 3.4, h, OK_PALE, false);
    text(s, r[0], 5.7, y + 0.15, 3.1, h - 0.3, { fontSize: 16 });
    text(s, r[1], 9.5, y + 0.15, 3.0, h - 0.3, { fontSize: 16 });
    text(s, "→", 9.0, y, 0.3, h, { fontSize: 20, color: MUTED, align: "center", valign: "middle" });
  });
}

// 카드 4장 + 아래 현재 상태 띠 (음성 · 포즈 · 박수 공통)
function fourCards(s, cards, noteLabel, noteBody) {
  const gap = 0.23, x0 = 0.6, w = (12.1 - gap * (cards.length - 1)) / cards.length;
  cards.forEach((c, i) => {
    const x = x0 + i * (w + gap);
    card(s, x, 2.0, w, 2.9, c[3], c[3] === CARD);
    labeled(s, x + 0.2, 2.2, w - 0.4, 2.5, c[0], c[1], c[2], 19, 17);
  });
  card(s, 0.6, 5.2, 12.1, 1.3, HOLD_PALE, false);
  text(s, [
    { text: noteLabel, options: { bold: true, color: HOLD } },
    { text: noteBody, options: { color: INK } },
  ], 0.9, 5.4, 11.5, 0.9, { fontSize: 16 });
}

// ── 9. 음성 ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "음성");
  fourCards(s, [
    ["모델", "faster-whisper medium (GPU). 소음을 고려해 small보다 높은 모델을 골랐다", INK, CARD],
    ["① 손등 3초", "손을 떼면 녹음이 끝난다. 소음 환경의 주력 방식", INK, CARD],
    ["② 웨이크워드", "무음 1.2초 뒤 자동 종료. 손을 쓸 수 없을 때 쓴다. 단어 \"웨이크\"는 임시값", INK, CARD],
    ["역할 분리", "Whisper는 받아쓰기만. 해석과 실행은 기존 명령 모듈(LLM)이 맡는다", OK, OK_PALE],
  ], "계기: ", "음성 인식이 어떻게 동작하는지 알아보고 싶어서 넣었다. 현재는 손등 트리거를 주력으로 쓴다.");
}

// ── 10. 포즈 ────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "포즈");
  fourCards(s, [
    ["라이브러리", "MediaPipe Pose. 이미 설치돼 있고 가시성 정보를 주며, 다중 인원 검출은 필요 없다", INK, CARD],
    ["22차원 특징", "정규화 좌표 9점 x 2, 팔꿈치 각도 2, 머리 방향 2. 박스는 관절 최소 · 최대로 직접 계산", INK, CARD],
    ["모드 분리", "손과 포즈를 한 번에 하나만 켜서 충돌을 막음. 명령 모듈은 공유하고 이름만 pose_*로 구분", OK, OK_PALE],
  ], "계기: ", "포즈 인식 참고 예제(YOLO)를 보고 우리 프로젝트에도 넣어 보고 싶었다. 지금은 특징 추출과 화면 표시까지 했고, 자세 등록과 인식은 다음 단계다.");
}

// ── 11. 박수 ────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "박수");
  fourCards(s, [
    ["가정", "소리 감지가 약해서 인식이 안 된다", MUTED, CARD],
    ["로그 확인", "박수 신호는 이미 정상으로 잡히고 있었다", INK, CARD],
    ["진짜 원인", "박수 신호는 약 30ms만 유지, 카메라는 33ms마다 한 프레임이라 겹칠 확률이 낮음. 박수 순간 양손이 하나로 검출되기도 함", FAIL, FAIL_PALE],
    ["해결", "동시를 요구하지 않고, 직전 1초 안에 양손이 모여 있었으면 인정", OK, OK_PALE],
  ], "결국: ", "양손 모으기 1초만으로 손 / 포즈 모드를 전환(설정으로 박수 요구 복귀 가능). 키보드 소리와 박수를 가르는 건 고주파 비율이 아니라 음량(peak)이었다.");
}

// ── 12. 교훈 ────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "교훈");
  const L = [
    ["고정 좌표 대신 비율", "어깨 너비 · 관절 거리로 나눠야 카메라 거리에 안 흔들린다"],
    ["순간과 유지를 구분", "스치듯 지나가는 전환 자세는 최소 유지시간으로 걸러낸다"],
    ["추측 말고 로그", "두 번 모두 짐작한 원인과 실제 원인이 달랐다"],
    ["2D 화면의 한계", "손과 몸을 돌리면 실제로 떨어져 있어도 겹쳐 보인다"],
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
}

pres.writeFile({ fileName: "assistant_devlog_v7.pptx" }).then((f) => console.log("saved:", f));
