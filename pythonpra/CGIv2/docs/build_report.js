// CGIv2 진행 보고서 (Word) 생성기 — 이 파일이 원본이다. docx 는 산출물.
//
// 실행 (docx npm 패키지가 있는 폴더를 NODE_PATH 로):
//   set NODE_PATH=<docx 가 설치된 node_modules>
//   node docs/build_report.js <출력 경로.docx>
// 그림은 outputs/report/*.jpg 를 읽는다.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, ShadingType, BorderStyle, ImageRun, LevelFormat, Footer, PageNumber,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const IMG = path.join(ROOT, "outputs", "report");
const OUT = process.argv[2] || path.join(ROOT, "outputs", "report", "CGIv2_진행보고서.docx");

const C = {
  ink: "17212B", muted: "5B6875", rule: "D6DCE3", accent: "B8323D",
  head: "E9EDF1", code: "EDF0F3", done: "1E7A4E", partial: "8F5D00", open: "5F6B77",
};
const FONT = { ascii: "Malgun Gothic", eastAsia: "맑은 고딕", hAnsi: "Malgun Gothic", cs: "Malgun Gothic" };
const MONO = { ascii: "Consolas", eastAsia: "맑은 고딕", hAnsi: "Consolas", cs: "Consolas" };
const PAGE_W = 11906, MARGIN = 1134, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 2cm 여백 → 9638 DXA
const IMG_MAX_PX = 640;                                               // 본문 폭 ≈ 6.69in ≈ 642px

// ── 글 조각 ─────────────────────────────────────────────────────────
// 문자열 또는 [{t, b, c, m}] (b = 굵게, c = 색, m = 고정폭)
function runs(x, base = {}) {
  const segs = typeof x === "string" ? [{ t: x }] : x;
  return segs.map((s) => new TextRun({
    text: s.t, bold: s.b || base.b, color: s.c || base.c, size: s.size || base.size,
    font: s.m ? MONO : undefined,
  }));
}
const P = (x, opt = {}) => new Paragraph({ children: runs(x, opt), ...opt.p });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (x) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(x) });
const note = (x) => new Paragraph({ style: "Note", children: runs(x) });
const code = (t) => new Paragraph({ style: "Code", children: [new TextRun({ text: t, font: MONO })] });
const caption = (x) => new Paragraph({ style: "Caption", children: runs(x) });

// ── 표 ──────────────────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 4, color: C.rule };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(x, w, { head = false, align, opt = {} } = {}) {
  // 문자열의 \n 은 칸 안에서 문단을 나눈다 — docx 는 텍스트 속 \n 을 줄바꿈으로 안 본다
  const parts = typeof x === "string" ? x.split("\n") : [x];
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders,
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: C.head } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: parts.map((part, i) => new Paragraph({
      alignment: align, spacing: { after: i < parts.length - 1 ? 60 : 0, line: 280 },
      children: runs(part, head ? { b: true, c: C.muted, size: 17 } : { size: 18, ...opt }),
    })),
  });
}
function table(headers, rows, ratios, { right = [] } = {}) {
  const sum = ratios.reduce((a, b) => a + b, 0);
  const widths = ratios.map((r) => Math.floor((TEXT_W * r) / sum));
  widths[widths.length - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const al = (i) => (right.includes(i) ? AlignmentType.RIGHT : AlignmentType.LEFT);
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { head: true, align: al(i) })) }),
      ...rows.map((r) => new TableRow({ children: r.map((x, i) => cell(x, widths[i], { align: al(i) })) })),
    ],
  });
}
const gap = () => new Paragraph({ spacing: { after: 60 }, children: [] });

// ── 그림 ────────────────────────────────────────────────────────────
// 크기(px)는 outputs/report 를 만들 때 기록한 값
const SIZES = {
  "p1_face.jpg": [1325, 420], "p1_place.jpg": [721, 900], "p1_paste.jpg": [1112, 460],
  "p1_shadow.jpg": [1206, 673], "p1_final.jpg": [2401, 640], "p2_refs.jpg": [1338, 220],
  "p2_bag.jpg": [1710, 558], "p2_car.jpg": [1683, 560], "p2_car_shadow.jpg": [2320, 300],
  "p2_watch.jpg": [1930, 520],
};
function figure(file, alt, cap, maxW = IMG_MAX_PX) {
  const [w, h] = SIZES[file];
  const W = Math.min(maxW, w), H = Math.round((W * h) / w);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
      children: [new ImageRun({
        type: "jpg", data: fs.readFileSync(path.join(IMG, file)),
        transformation: { width: W, height: H },
        altText: { title: alt, description: alt, name: file },
      })],
    }),
    caption(cap),
  ];
}

// ── 내용 ────────────────────────────────────────────────────────────
const children = [
  // 제목
  new Paragraph({ style: "Eyebrow", children: [new TextRun("CGIv2 · 내부 테스트용 · 2026-09-26 작업까지")] }),
  new Paragraph({ style: "Title", children: [new TextRun("CGIv2 진행 보고서")] }),
  P("AnyDoor의 학습된 가중치는 그대로 두고, 그 앞뒤 처리를 직접 만들어 합성 파이프라인을 세웠습니다. 1안(내 사진을 명소에)은 배치부터 생성, 얼굴 복원, 되붙이기, 그림자까지 자동으로 돌아갑니다. 2안(사람 사진에 가방·시계·자동차)은 세 물건 모두 첫 시도를 마쳤습니다.", { p: { spacing: { after: 200 } } }),
  table(["안", "내용", "상태"], [
    [[{ t: "1안", b: true }], "국내외 명소 사진에 내 사진(사람) 넣기 — 얼굴 정체성 유지가 핵심", [{ t: "동작", b: true, c: C.done }]],
    [[{ t: "2안", b: true }], "사람 사진에 가방 · 시계 · 자동차 넣기 — 세 물건 첫 결과, 다듬는 중", [{ t: "시도", b: true, c: C.partial }]],
    [[{ t: "3안", b: true }], "퍼스널컬러 (예비)", [{ t: "대기", b: true, c: C.open }]],
  ], [1, 7, 1.2]),

  // 1
  H1("1. 설계 원칙 — 가중치는 건드리지 않는다"),
  P("AnyDoor는 SD 2.1 U-Net, ControlNet, DINOv2 ViT-g/14로 이뤄져 있습니다. 참조 이미지를 이해하는 경로가 DINOv2 하나뿐이라, 이 인코더를 바꾸면 전체 2,452M 파라미터 중 VAE 84M(3.4%)만 쓸모가 남습니다. 그래서 가중치는 고정하고, 바꿔도 되는 부분만 직접 만듭니다. 예전 CGI(v1)는 SD 1.5 inpainting 기반이라 AnyDoor 가중치를 쓸 수 없어서, 이 구조로 CGIv2를 새로 세웠습니다."),
  table(["등급", "뜻", "해당하는 것"], [
    [[{ t: "자유", b: true, c: C.done }], "입출력만 맞으면 바꿔도 된다", "마스크 생성, 배치, 얼굴 복원, 되붙이기, 그림자, 평가, 샘플러"],
    [[{ t: "규약", b: true, c: C.partial }], "바꾸면 에러 없이 품질만 떨어진다", "참조 224 정사각 · 흰 배경, 타깃 512 크롭, Sobel 디테일 맵"],
    [[{ t: "고정", b: true, c: C.accent }], "바꾸면 가중치가 무의미해진다", "DINOv2, ControlNet 구조, U-Net, VAE, 노이즈 스케줄"],
  ], [1, 3, 5]),
  gap(),
  P([{ t: "AnyDoor 저장소는 고치지 않고 불러다 쓰기만 합니다. 10GB GPU에서 돌리기 위한 AnyDoor 쪽 패치는 따로 적용해 두었고 문서로 남겼습니다.", c: C.muted }]),

  // 2
  H1("2. 파이프라인 — 3단계"),
  P("환경이 둘로 나뉘어 3단계로 돕니다. AnyDoor venv(OpenCV 4.7.0, transformers 4.19.2)에서는 얼굴 검출기 YuNet이 크래시하고 Mask2Former가 없습니다. 그래서 계산은 CGI venv에서 하고, 확산 생성만 AnyDoor venv에서 합니다. 1안과 2안이 같은 3단계를 쓰고, 1단계의 배치 방식만 다릅니다."),
  table(["단계", "환경", "하는 일"], [
    [[{ t: "1. 배치", b: true }], "CGI venv", "1안: 지면 분할(Mask2Former) + 기존 관광객(DETR) → 원근 → 발 위치·키\n2안: 관절(Keypoint R-CNN) → 손·손목 기준 박스\n자동차: 1안 배치 × (차 높이 / 사람 키)"],
    [[{ t: "2. 생성", b: true, c: C.accent }], "AnyDoor venv", "참조 마스크(BiRefNet) · 면적 정규화 → AnyDoor 입력 규약(224 / 512) → DINOv2 → ControlNet → U-Net → DDIM → VAE → 512 결과 저장. 가중치는 여기서만 쓴다"],
    [[{ t: "3. 마감", b: true }], "CGI venv", "원래 크기로 복원 → 얼굴 이식(YuNet + SFace, 1안) → 사람·물건만 되붙이기(BiRefNet + Blur-Fusion) → 접지 그림자"],
  ], [1.2, 1.5, 6.3]),
  gap(),
  P("생성은 한 쌍에 약 3.3분(10GB GPU, 모델 로딩 약 110초 별도), 3단계 후처리는 한 장에 1~2초입니다. 3단계는 저장된 512 결과로 다시 돌릴 수 있어서, 후처리를 바꿀 때 확산을 다시 돌리지 않습니다."),

  // 3
  H1("3. 1안 — 명소 사진에 내 사진"),
  P("한 단계를 풀면 그전까지 가려져 있던 문제가 드러났고, 그 순서대로 풀어 왔습니다."),
  table(["날짜", "드러난 문제", "해결", "결과"], [
    ["09-21", "AnyDoor 원본 버그 3개(패딩 표식, 크롭 난수, 1px 밀림), 마스크 생성 기능 없음", "입력 처리를 하나로 합치고 BiRefNet으로 마스크 생성", "원본 대 CGIv2 3×3 비교"],
    ["09-21", "정체성 점수가 사람이 아니라 배경을 재고 있었음", "배경을 지운 뒤 측정", "믿을 수 있는 기준선"],
    ["09-22", "얼굴 정체성 0.107 (같은 사람 판정 기준 0.363)", "상반신 크롭은 0.131로 부족 → 원본 얼굴을 정렬해 이식", [{ t: "0.95", b: true, c: C.accent }]],
    ["09-23", "사람이 떠 있거나 크기가 틀림", "지면 분할 + 원근 추정(Hoiem 2006), 삼등분선, 기존 관광객 피하기", "4건 모두 발이 땅에 닿음"],
    ["09-23", "랜드마크가 저해상도로 다시 그려짐 (크롭이 화면의 41~67%)", "사람 부분만 원본 배경 위에 되붙임", [{ t: "배경 선명도 9~31% → " }, { t: "100%", b: true, c: C.accent }]],
    ["09-26", "되붙이기 뒤 발밑이 떠 보임", "발밑 접지 그림자", "4건 모두 땅에 닿아 보임"],
  ], [0.8, 3, 3, 2]),
  ...figure("p1_face.jpg", "참조 얼굴, AnyDoor만 쓴 얼굴, 얼굴 이식 후 얼굴 비교",
    [{ t: "그림 1. 얼굴 정체성. ", b: true, c: C.ink }, { t: "AnyDoor는 물건 수준 모델이라 참조를 224px로 줄이면서 얼굴 정보를 잃습니다(SFace 0.19). 참조 얼굴을 5점 랜드마크로 정렬해 이식하면 0.95가 됩니다. 판정 기준은 0.363입니다." }]),
  ...figure("p1_place.jpg", "에펠탑 광장의 배치 점검 화면", [{ t: "그림 2. 배치 점검. ", b: true, c: C.ink }, { t: "초록은 걸을 수 있는 지면, 파랑은 기존 관광객, 빨간 선은 지평선, 노란 박스는 배치입니다. 관광객 22명의 키와 발 위치로 원근을 맞춰 그 자리의 사람 키를 정합니다." }], 300),
  ...figure("p1_paste.jpg", "에펠탑 아래: 크롭 되붙이기와 사람만 되붙이기 비교", [{ t: "그림 3. 되붙이기. ", b: true, c: C.ink }, { t: "AnyDoor는 512 크롭 전체를 다시 그려서 탑의 격자와 관광객이 뭉개졌습니다(왼쪽). 사람만 분할해 되붙이면 나머지는 원본 픽셀 그대로입니다(오른쪽). AnyDoor 원저자도 데모 코드에서는 박스 밖을 원본으로 되돌려 두었습니다." }]),
  ...figure("p1_shadow.jpg", "네 배경의 발 부분: 그림자 없음과 접지 그림자", [{ t: "그림 4. 접지 그림자. ", b: true, c: C.ink }, { t: "왼쪽은 그림자 없음, 오른쪽은 접지 그림자입니다. 해 방향을 따라 몸이 드리우는 그림자도 만들었지만, 장면 속 사람들의 그림자로 해를 자동 추정하는 방식이 20개 배경 중 한 곳도 잡지 못해 선택 기능으로 둡니다." }], 520),
  ...figure("p1_final.jpg", "1안 최종 결과 4장", [{ t: "그림 5. 1안 최종 4장. ", b: true, c: C.ink }, { t: "수원 화성길 K05, 에펠탑 W01, 산토리니 W05, 브란덴부르크 문 W09입니다. 얼굴 정체성은 0.86~0.95입니다." }]),
  P([{ t: "전신을 크게 넣을 수 없는 배경이 5개 있습니다(K06 · W03 · W06 · W08 · W10). 높은 곳에서 내려다보거나 올려다본 사진이라 원근상 전신이 화면의 1% 미만이 됩니다.", c: C.muted }]),

  // 4
  H1("4. 2안 — 사람 사진에 가방 · 시계 · 자동차"),
  P("1안은 장면(지면과 원근)을 보고 사람을 세웠습니다. 2안은 반대로 사람의 몸(관절)을 보고 물건을 붙입니다. 관절 검출은 CGI venv에 이미 있는 torchvision의 Keypoint R-CNN(COCO 17점)을 써서 새 패키지를 설치하지 않았습니다. 물건 사진은 Unsplash에서 후보 목록을 먼저 확인한 뒤 받았고, 가방은 AnyDoor 예제의 백팩을 씁니다."),
  ...figure("p2_refs.jpg", "2안 참조 물건 5개", [{ t: "그림 6. 참조 물건. ", b: true, c: C.ink }, { t: "시계 A01 · A03, 자동차 C01 · C03(Unsplash), 가방 B01(AnyDoor 예제)입니다. 뚜껑 열린 점자 시계와 위에서 내려다본 차 사진은 받은 뒤 뺐습니다." }]),
  table(["물건", "배치 기준", "결과", "남은 문제"], [
    [[{ t: "가방", b: true }], "팔이 내려온 손목에 매단다", "가방 재현은 참조와 같음. 손을 덮어 쥔 모습으로 읽힘", "손가락이 보이는 쥔 모습, 어깨에 멘 모습"],
    [[{ t: "자동차", b: true }], "1안 배치 × 차 높이 비율 (세단 0.85, 스포츠카 0.76)", "멀어지는 스포츠카(K08)가 자연스러움. 차용 접지 그림자로 땅에 붙음", "다른 차를 피하지 못함, 스튜디오 조명"],
    [[{ t: "시계", b: true }], "손목 둘레만 잘라 합성 후 되붙임, 줄 축을 팔뚝과 직각으로", "드러난 손목(F04)은 전신 크기에서 찬 것처럼 보임", "확대하면 손등 쪽 치우침, 기존 팔찌 잔존, 문자판 각도"],
  ], [1, 2.6, 3, 2.6]),

  H2("4.1 가방"),
  ...figure("p2_bag.jpg", "참조 백팩과 두 남성 사진에 가방을 든 결과", [{ t: "그림 7. 가방. ", b: true, c: C.ink }, { t: "버건디 색, 지퍼 주머니, 패치, 스트랩까지 참조와 같습니다. 사람 얼굴과 달리 물건은 AnyDoor가 원래 잘하는 분야입니다." }]),
  bullet("가방 박스 밖에서 바뀐 면적은 0.2~0.5%입니다(크롭 전체 되붙이기는 4.6~14.2%). 사람 분할 되붙이기가 물건에도 그대로 통합니다."),
  bullet("두 손을 카디건 주머니에 넣은 사진(F12)은 팔뚝 각도(몸 쪽 22°)와 손목 높이(엉덩이보다 키 × 0.075 위)로 걸러 건너뜁니다."),

  H2("4.2 자동차"),
  ...figure("p2_car.jpg", "전주 골목 원본과 스포츠카·세단 합성, 북촌 골목 합성", [{ t: "그림 8. 자동차. ", b: true, c: C.ink }, { t: "차가 다니는 골목(K08 전주, K07 북촌)에 넣었습니다. 크기는 원근이 줍니다. 그 자리에 선 사람 키에 '차 높이 / 사람 키'를 곱합니다. 오른쪽 차선을 멀어지는 스포츠카가 가장 자연스럽고, 세단은 주차된 차를 가립니다(배치가 사람만 피해서입니다)." }]),
  ...figure("p2_car_shadow.jpg", "흰 세단 아래: 사람용과 차용 접지 그림자", [{ t: "그림 9. 차용 접지 그림자. ", b: true, c: C.ink }, { t: "사람 발 기준 값(진하기 0.5, 두께 0.03)으로는 차체 밑이 밝아 떠 보였습니다(왼쪽). 진하기 0.7, 두께 0.08로 올리니 땅에 붙습니다(오른쪽). 색 정합 0.3도 시험했지만 노란 차가 탁한 올리브색으로 바뀌어 2안에서는 쓰지 않습니다." }]),

  H2("4.3 시계"),
  ...figure("p2_watch.jpg", "정장 남성 전신 결과와 손목 확대", [{ t: "그림 10. 시계. ", b: true, c: C.ink }, { t: "전신 사진에서 문자판은 45~52px이라 AnyDoor 면적 관문(1%)에 못 미칩니다. 손목 둘레(박스 긴 변 × 6)만 잘라 그 안에서 합성하고 원래 사진에 되붙입니다. 전신 크기에서는 찬 것처럼 보이지만, 확대하면 손등 쪽으로 조금 내려와 있고 원래 팔찌가 남아 있습니다." }]),
  note([{ t: "고친 버그. ", b: true, c: C.accent }, { t: "처음에는 시계 네 개가 모두 정장 소매 위에 올라갔습니다. 관절 모델의 손목 점이 실제 손목이 아니라 소매 끝에 찍히기 때문입니다(키의 2~3% 위). 박스를 그려 보고 생성을 중단한 뒤 손 쪽으로 옮겨 다시 돌렸습니다." }]),

  // 5
  H1("5. 숫자로 본 진척"),
  table(["항목", "값", "비고"], [
    ["얼굴 정체성 (SFace)", [{ t: "0.107 → " }, { t: "0.86~0.95", b: true, c: C.accent }], "같은 사람 판정 기준 0.363"],
    ["생성 범위 안 배경 선명도", [{ t: "9~31% → " }, { t: "100%", b: true, c: C.accent }], "라플라시안 분산, 원본 대비"],
    ["발 접지 (1안 합성 4건)", "4 / 4", "배경 20개 점검, 전신 부적합 5개 표시"],
    ["생성 시간", "약 3.3분 / 쌍", "10GB GPU, 50 steps, 모델 로딩 약 110초 별도"],
    ["3단계 후처리", "1~2초 / 장", "확산 없이 다시 돌릴 수 있음"],
    ["2안 가방 · 박스 밖 변화", "0.2~0.5%", "크롭 전체 되붙이기는 4.6~14.2%"],
    ["2안 시계 부분 이미지", "336~402px", "박스 면적 2.4~2.5%, 관문 통과"],
    ["해 자동 추정", "0 / 20", "그래서 드리운 그림자는 선택 기능"],
  ], [3, 2.4, 4], { right: [1] }),

  // 6
  H1("6. 남은 과제"),
  table(["우선", "과제", "내용"], [
    [[{ t: "다음", b: true, c: C.partial }], "2안 자동차가 다른 차를 피하게", "지금 배치는 사람만 피한다. DETR의 car 클래스도 겹침 제외에 넣는다"],
    [[{ t: "다음", b: true, c: C.partial }], "2안 조명 맞추기", "스튜디오 참조가 볕 드는 장면에서 고르게 밝다. 색 정합은 제품 색을 바꿔서 못 쓰고, 밝기(L)만 맞추는 도구가 필요하다"],
    [[{ t: "다음", b: true, c: C.partial }], "2안 시계 다듬기", "소매 쪽으로 붙이기, 기존 장신구를 교체하기, 드러난 손목이 있는 사진 고르기"],
    [[{ t: "준비", b: true, c: C.open }], "2안 가방 자세", "손가락이 보이는 쥔 모습, 어깨에 멘 모습"],
    [[{ t: "준비", b: true, c: C.open }], "1안 배치 다듬기", "지면 경계(연석) 피하기, 다리가 잘리는 구도(5개 배경), 드리운 그림자의 빛 방향을 UI에서 고르기"],
    [[{ t: "준비", b: true, c: C.open }], "1안 얼굴", "얼굴 색 맞추기, 옆얼굴에서도 이식이 버티는지 확인"],
    [[{ t: "대기", b: true, c: C.open }], "3안 퍼스널컬러", "시작 전"],
  ], [0.9, 2.6, 5.5]),

  // 7
  H1("7. 실행 방법"),
  P("CGIv2 폴더에서 실행합니다. 1안은 아래 세 줄입니다. 2안은 1단계만 check_anchor.py(가방·시계)나 check_placement.py --height-scale(자동차)로 바뀌고, 명령 전체는 README에 있습니다."),
  P([{ t: "1단계 · 배치 (CGI venv)", b: true }]),
  code("D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/check_placement.py"),
  P([{ t: "2단계 · 생성 (AnyDoor venv)", b: true }]),
  code("D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/gen_placed.py --object F01 --backgrounds K05 W01 W05 W09"),
  P([{ t: "3단계 · 마감 (CGI venv)", b: true }]),
  code("D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py"),
  P([{ t: "2안 자동차 3단계 예 · 차용 접지 그림자", b: true }]),
  code("D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py --work work/plan2/gen_car --out outputs/plan2/car_v2 --paste object --shadow contact --contact-strength 0.7 --contact-width 1.05 --contact-height 0.08 --no-face --obj-dir work/plan2/raw --mask-dir work/plan2/masks"),

  // 8
  H1("8. 기록 위치"),
  table(["파일", "내용"], [
    [[{ t: "CGIv2/CHANGELOG.md", m: true }], "모든 변경을 값 하나까지. 기술·도구 등록부와 상수 등록부 포함"],
    [[{ t: "CGIv2/README.md", m: true }], "코드 구조, 1안 · 2안 실행 명령"],
    [[{ t: "CGI/docs/anydoor_local_10gb.md", m: true }], "10GB GPU 실행 패치 7가지와 되돌리는 법"],
    [[{ t: "Downloads/AnyDoor_재사용_설계.docx", m: true }], "가중치 재사용 설계 문서"],
    [[{ t: "CGIv2/outputs/placed/", m: true }], "1안 최종 결과 (*_final.png)"],
    [[{ t: "CGIv2/outputs/plan2/", m: true }], "2안 결과 (object 가방, car_v2 자동차, watch 시계)"],
    [[{ t: "CGIv2/work/plan2/raw/_credits.json", m: true }], "Unsplash 사진 출처"],
    [[{ t: "CGIv2/docs/build_report.js", m: true }], "이 문서의 생성 스크립트 (그림은 outputs/report/)"],
  ], [4, 5]),
];

const doc = new Document({
  creator: "CGIv2",
  title: "CGIv2 진행 보고서",
  description: "AnyDoor 가중치 재사용 합성 파이프라인 1안·2안 진행 상황",
  styles: {
    default: {
      document: { run: { font: FONT, size: 20, color: C.ink }, paragraph: { spacing: { line: 312, after: 120 } } },
    },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 44, bold: true, color: C.ink }, paragraph: { spacing: { after: 160 } } },
      { id: "Eyebrow", name: "Eyebrow", basedOn: "Normal", next: "Normal",
        run: { size: 16, color: C.muted, characterSpacing: 20 }, paragraph: { spacing: { after: 60 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: C.ink },
        paragraph: { spacing: { before: 420, after: 160 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: C.ink },
        paragraph: { spacing: { before: 280, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
        run: { size: 17, color: C.muted }, paragraph: { spacing: { before: 40, after: 220 } } },
      { id: "Code", name: "Code", basedOn: "Normal", next: "Normal",
        run: { font: MONO, size: 16 },
        paragraph: { spacing: { before: 40, after: 160, line: 264 },
          shading: { type: ShadingType.CLEAR, color: "auto", fill: C.code },
          border: { left: { style: BorderStyle.SINGLE, size: 12, color: C.rule, space: 6 } } } },
      { id: "Note", name: "Note", basedOn: "Normal", next: "Normal",
        run: { size: 19 },
        paragraph: { spacing: { before: 80, after: 200 }, indent: { left: 200, right: 200 },
          shading: { type: ShadingType.CLEAR, color: "auto", fill: "F6E4E6" } } },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 400, hanging: 240 } } } }],
    }],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: ["CGIv2 진행 보고서 · ", PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 16, color: C.muted }),
      ] })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, buf);
  console.log("저장:", OUT, `(${(buf.length / 1024).toFixed(0)} KB)`);
});
