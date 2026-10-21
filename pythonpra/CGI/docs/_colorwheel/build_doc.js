// 상의 색 변경(색상환) 동작 방식 (Word) 생성기 — 이 파일이 원본이다. docx는 산출물.
//
// 실행 (docx npm 패키지가 있는 폴더를 NODE_PATH로, 그림은 먼저 make_figures.py로 만든다):
//   set NODE_PATH=<docx가 설치된 node_modules>
//   node docs/_colorwheel/build_doc.js [출력 경로.docx]
//
// 내용 근거: moalocal/moa_app 코드(results.py, ColorWheel.jsx), moalocal/colorwheel/index.html,
// 10-20 실행 기록(moa_app/storage의 추출·작업 기록). 동작 방식만 다룬다 — 문제점과 다음 단계는 CGI_색상환_정리.md.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, ImageRun, VerticalAlign,
} = require("docx");

const HERE = __dirname;
const CGI = path.resolve(HERE, "..", "..");
const OUT = process.argv[2] || path.join(CGI, "docs", "CGI_색상환_동작방식.docx");

const C = { ink: "17212B", muted: "5B6875", rule: "D6DCE3", accent: "1F5FAD", head: "E9EDF1" };
const FONT = { ascii: "Malgun Gothic", eastAsia: "맑은 고딕", hAnsi: "Malgun Gothic", cs: "Malgun Gothic" };
const MONO = { ascii: "Consolas", eastAsia: "맑은 고딕", hAnsi: "Consolas", cs: "Consolas" };
const PAGE_W = 11906, MARGIN = 1134, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 2cm 여백 → 9638 DXA

// ── 글 조각 — 문자열 또는 [{t, b, c, mono}] ──────────────────────────────
function runs(x, base = {}) {
  const segs = typeof x === "string" ? [{ t: x }] : x;
  return segs.map((s) => new TextRun({
    text: s.t, bold: s.b || base.b, color: s.c || base.c, size: s.size || base.size,
    font: s.mono ? MONO : undefined,
  }));
}
const P = (x, opt = {}) => new Paragraph({ children: runs(x, opt), ...opt.p });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (x) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(x) });
const step = (x) => new Paragraph({ numbering: { reference: "steps", level: 0 }, children: runs(x) });
const note = (x) => P(x, { c: C.muted, size: 18, p: { spacing: { before: 100, after: 60 } } });
const code = (t) => ({ t, mono: true });
const b = (t) => ({ t, b: true });

// ── 표 ──────────────────────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 4, color: C.rule };
const borders = { top: border, bottom: border, left: border, right: border };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: none, bottom: none, left: none, right: none };
function toParas(x) {              // \n에서 문단을 나눈다 (docx는 \n을 줄바꿈으로 안 본다)
  const segs = typeof x === "string" ? [{ t: x }] : x;
  const paras = [[]];
  for (const s of segs) {
    s.t.split("\n").forEach((piece, i) => {
      if (i > 0) paras.push([]);
      if (piece) paras[paras.length - 1].push({ ...s, t: piece });
    });
  }
  return paras;
}
function cell(x, w, head, size) {
  const parts = toParas(x);
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders,
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: C.head } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    children: parts.map((segs, i) => new Paragraph({
      spacing: { after: i < parts.length - 1 ? 50 : 0, line: 280 },
      children: runs(segs, head ? { b: true, c: C.muted, size: size - 1 } : { size }),
    })),
  });
}
function widthsOf(ratios) {
  const sum = ratios.reduce((a, c) => a + c, 0);
  const w = ratios.map((r) => Math.floor((TEXT_W * r) / sum));
  w[w.length - 1] += TEXT_W - w.reduce((a, c) => a + c, 0);
  return w;
}
function table(headers, rows, ratios, size = 18) {
  const widths = widthsOf(ratios);
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true, size)) }),
      ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((x, i) => cell(x, widths[i], false, size)) })),
    ],
  });
}
const gap = () => new Paragraph({ spacing: { after: 60 }, children: [] });

// ── 그림 ────────────────────────────────────────────────────────────────
// png 머리에서 크기를 읽어 가로 폭(px)에 맞춘다
function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { buf, w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}
function image(name, widthPx) {
  const { buf, w, h } = pngSize(path.join(HERE, name));
  return new ImageRun({ type: "png", data: buf, transformation: { width: widthPx, height: Math.round((h * widthPx) / w) } });
}
// 그림 여러 장을 한 줄에: [{file, caption}]
function figureRow(items, widthPx) {
  const widths = widthsOf(items.map(() => 1));
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ cantSplit: true, children: items.map((it, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      borders: noBorders,
      margins: { top: 40, bottom: 40, left: 60, right: 60 },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [image(it.file, widthPx)] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: runs(it.caption, { size: 18, c: C.muted }) }),
      ],
    })) })],
  });
}

// ── 본문 ────────────────────────────────────────────────────────────────
const children = [
  new Paragraph({ style: "Eyebrow", children: [new TextRun("CGI · moa 복사본 (moalocal/moa_app) · 2026-10-21")] }),
  new Paragraph({ style: "Title", children: [new TextRun("상의 색 변경(색상환) 동작 방식")] }),
  P("합성 결과 화면에서 '색 변경'을 누르면, 새로 입힌 상의만 고른 색으로 바뀌어 보입니다. 이 문서는 동작 방식만 다룹니다. 문제점과 다음 단계는 CGI_색상환_정리.md에 있습니다."),

  H1("1. 전체 흐름"),
  table(["단계", "어디서", "하는 일"], [
    ["1", "화면", "합성이 끝나 결과 화면이 뜹니다"],
    ["2", "화면", "'색 변경'을 누르면 색 변경 팝업이 열립니다"],
    ["3", "서버 (SAM2)", "합성 결과에서 새 상의 윤곽을 찾습니다. 결과마다 처음 한 번만 찾고, 찾은 윤곽은 저장해서 다시 씁니다"],
    ["4", "브라우저", "결과 사진과 윤곽으로 색 계산을 준비합니다 (상의 화소의 LAB 값과 평균)"],
    ["5", "브라우저", "색상환과 밝기 막대로 색을 고를 때마다 상의 화소를 다시 칠합니다"],
    ["6", "화면", "닫으면 끝납니다. 바꾼 색은 저장하지 않습니다"],
  ], [0.7, 1.5, 7.8]),
  gap(),
  figureRow([
    { file: "ex1_result.png", caption: "① 합성 결과" },
    { file: "ex1_mask.png", caption: "② 찾은 상의 윤곽 (파란 선)" },
    { file: "ex1_recolor.png", caption: "③ #4B6134 (밝기 38%)로 바꾼 모습" },
  ], 190),
  note("예시 1: 10-20 실행에서 헨리넥을 입힌 결과(res_4a45b5b5b714)를 색 변경 팝업에서 초록으로 바꾼 것입니다. 그림은 팝업에서 고른 색을 같은 결과에 같은 계산식으로 다시 적용해 만들었고, 팝업에 뜬 상의 화소 수, 평균 밝기, 평균 색이 모두 같습니다."),

  H1("2. 상의 윤곽 찾기 (서버)"),
  P("색은 새로 입힌 상의 안에서만 바꿔야 합니다. 그래서 먼저 합성 결과 사진에서 상의의 실제 테두리를 찾습니다."),
  H2("순서"),
  step("합성할 때 4단계에서 지정한 입힐 영역(작업 기록의 area_mask)을 불러와 결과 사진 크기에 맞춥니다."),
  step("입힐 영역을 감싸는 사각형을 만들고, 사방에 사진 긴 변의 3%만큼 여유를 둡니다."),
  step("이 사각형을 SAM2의 박스 프롬프트로 넣어, 합성 결과 사진에서 상의를 찾습니다. 점은 쓰지 않습니다."),
  step("찾은 상의 크기가 입힐 영역의 0.3~2배를 벗어나면 잘못 찾은 것으로 보고 실패로 돌려줍니다."),
  step([{ t: "성공하면 " }, code("결과번호_garment.png"), { t: "로 저장합니다. 같은 결과에서 다시 누르면 SAM2를 돌리지 않고 이 파일을 줍니다." }]),
  note("dev-cej 브랜치 restore의 find_garment와 같은 방식, 같은 값입니다. GPU는 추출, 합성과 같은 차례(GPU_LOCK)로 씁니다."),

  H2("기존 입힐 영역을 그대로 칠하지 않는 이유"),
  P("입힐 영역은 원래 옷이 있던 자리이고, 새 상의는 AnyDoor가 그 자리에 새로 그린 것입니다. AnyDoor는 영역을 감싸는 사각형 안을 다시 그리기 때문에('영역 모양 유지'를 끈 경우), 새 상의 모양이 영역과 정확히 같지 않습니다."),
  table(["경우", "입힐 영역을 그대로 칠하면"], [
    ["새 상의가 영역보다 작을 때 (예: 크롭티)", "영역 안의 피부, 배경, 원래 옷 남은 조각까지 칠해집니다"],
    ["새 상의가 영역보다 클 때", "영역 밖으로 나온 소매, 밑단, 칼라는 원래 색으로 남습니다"],
    ["경계", "브러시로 다듬은 영역 선이 새 상의 테두리와 맞지 않아 색이 번집니다"],
  ], [3.5, 6.5]),
  note("그래서 입힐 영역은 새 상의를 찾는 힌트(사각형)로만 씁니다. '영역 모양 유지'(Shape Control)를 켜고 합성했다면 새 상의가 영역 모양을 따르므로, 영역과 비교적 잘 맞습니다."),

  H2("실패할 때"),
  bullet([{ t: "입힐 영역 기록이 없으면 " }, code("404 SOURCE_NOT_FOUND"), { t: ", 상의를 못 찾거나 크기가 범위를 벗어나면 " }, code("400 GARMENT_NOT_FOUND"), { t: "를 돌려줍니다. 팝업에는 그 문구가 뜹니다." }]),
  bullet("크기는 범위 안인데 모양이 틀린 경우는 걸러지지 않습니다."),

  H1("3. 색 고르기 (화면)"),
  new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widthsOf([3, 7]),
    rows: [new TableRow({ cantSplit: true, children: [
      new TableCell({
        width: { size: widthsOf([3, 7])[0], type: WidthType.DXA }, borders: noBorders, verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [image("wheel.png", 170)] })],
      }),
      new TableCell({
        width: { size: widthsOf([3, 7])[1], type: WidthType.DXA }, borders: noBorders, verticalAlign: VerticalAlign.CENTER,
        margins: { left: 160 },
        children: [
          bullet([b("원형 색상환"), { t: ": 각도 = 색상(0~360°, 오른쪽 빨강부터 시계 방향), 중심에서 거리 = 진하기(채도, 중심 흰색 0 → 테두리 1)" }]),
          bullet([b("밝기 막대"), { t: ": 명도 0~100%. 막대를 옮기면 색상환 전체 밝기도 같이 바뀝니다" }]),
          bullet([b("고른 색 표시"), { t: ": 견본, HEX, RGB, 밝기 L" }]),
          bullet([b("버튼"), { t: ": 원래 색으로(고른 색 취소), 누르는 동안 원래 결과(비교용), 닫기" }]),
        ],
      }),
    ] })],
  }),
  note("왼쪽 그림은 예시 2의 #FF89D6을 고른 상태입니다 (색상 약 321°, 진하기 0.46, 밝기 100%)."),

  H1("4. 색 바꾸기 계산 (브라우저)"),
  P("계산은 모두 브라우저 안에서 합니다. 서버는 윤곽만 줍니다."),
  H2("준비 (팝업이 열릴 때 한 번)"),
  bullet("결과 사진과 윤곽을 긴 변 1200px 이하 사본으로 줄입니다. 색상환 위를 끌면서 고르는 동안에도 바로 보이게 하기 위해서입니다."),
  bullet("윤곽은 흑백 값이 127보다 큰 곳을 상의로 봅니다."),
  bullet("경계 섞는 비율: 화소마다 주변 3×3(9칸) 중 상의인 칸의 비율(0~1)입니다. 상의 안쪽은 1, 테두리는 1보다 작습니다."),
  bullet("상의 화소(비율 > 0)를 sRGB에서 CIE LAB(D65)로 바꾸고, 안쪽 화소(비율 = 1)로 평균 L, a, b를 구합니다."),
  H2("칠하기 (색을 고를 때마다)"),
  P("고른 색을 LAB로 바꾼 값을 (Lt, at, bt)라 하면, 상의 화소마다 아래처럼 바꿉니다.", { p: { keepNext: true } }),
  table(["값", "계산", "뜻"], [
    ["밝기 L'", [code("Lt + (L − 평균 L)"), { t: "\n0~100으로 자름" }], "원래 명암 차이(주름, 그림자)는 그대로 두고, 평균 밝기만 고른 색으로 옮깁니다"],
    ["색 a'", [code("at + 0.5 × (a − 평균 a)")], "원래 색 차이를 절반만 남깁니다"],
    ["색 b'", [code("bt + 0.5 × (b − 평균 b)")], "원래 색 차이를 절반만 남깁니다"],
    ["최종 화소", [code("원래 × (1 − 비율) + 새 색 × 비율")], "테두리는 원래 색과 섞어 경계를 부드럽게 합니다"],
  ], [1.4, 3.8, 4.8]),
  gap(),
  bullet("(L', a', b')를 다시 sRGB로 바꿔 칠합니다."),
  bullet("색상환 위를 끌면서 고르는 동안 값이 여러 번 바뀌어도, 한 화면(프레임)에 한 번만 계산합니다."),
  bullet("고른 색의 밝기가 원래 상의 평균보다 35 넘게 밝으면 '주름과 명암이 약하게 보일 수 있다'는 안내를 띄웁니다."),
  note("색 차이를 절반만 남기는 것은 원래 옷의 색 얼룩이 새 색 위로 비치지 않게 하기 위해서입니다. 대신 무늬 색끼리의 차이도 줄어듭니다."),

  H2("예시로 본 계산"),
  table(["", "예시 1 헨리넥", "예시 2 줄무늬 유니폼"], [
    ["결과 번호", [code("res_4a45b5b5b714")], [code("res_5c73cc29b6c8")]],
    ["상의 화소 (경계 포함)", "291,700", "229,689"],
    ["원래 상의 평균", "밝기 L 52.6 · 색 #827D75", "밝기 L 24.3 · 색 #552954"],
    ["고른 색", "#4B6134 (밝기 막대 38%) · L 38", "#FF89D6 (밝기 막대 100%) · L 72"],
    ["평균 밝기 변화", "−14.3 (어둡게)", "+48.0 (밝게)"],
    ["밝기 안내 문구 (+35 초과)", "안 뜸", "뜸"],
  ], [2.6, 3.7, 3.7]),
  gap(),
  figureRow([
    { file: "ex2_result.png", caption: "예시 2 원래 결과" },
    { file: "ex2_recolor.png", caption: "#FF89D6으로 바꾼 모습" },
  ], 230),
  note("예시 2처럼 여러 색이 섞인 무늬는 줄마다 밝기 차이는 남지만, 색 차이가 절반으로 줄어 전부 분홍 계열이 됩니다. 원래 평균 밝기보다 48 밝은 색이라 안내 문구가 떴습니다."),

  H1("5. 걸리는 시간"),
  P("10-20 실행 기록(moa_app/storage) 기준입니다. SAM2만 따로 잰 기록은 없어서, 같은 PC의 추출 기록으로 대신했습니다."),
  table(["상황", "시간", "근거"], [
    ["같은 결과를 두 번째 열 때", "거의 0초", "저장해 둔 윤곽을 씀"],
    ["처음 열 때 (보통)", "1초 안팎 (SAM2 0.4~0.6초)", "1024×1024 추출 기록 0.38~0.59초"],
    ["서버를 막 켜서 SAM2가 아직 안 불러졌을 때", "약 8초", "첫 추출 기록 8.1초 (모델 불러오기 포함)"],
    ["다른 합성이 돌고 있을 때", "그 합성이 끝날 때까지 (1~2분)", "같은 GPU 차례. 합성 기록 58초~1분 56초"],
    ["서버 켠 직후 AnyDoor 예열 중", "예열이 끝날 때까지 (몇 분)", "예열도 GPU 차례를 잡음"],
  ], [3.6, 2.9, 3.5]),
  note("팝업이 열린 뒤 색을 바꾸는 계산은 브라우저에서 하므로 서버를 기다리지 않습니다."),
];

const doc = new Document({
  creator: "CGI",
  title: "상의 색 변경(색상환) 동작 방식",
  description: "합성 결과에서 새로 입힌 상의만 색을 바꾸는 기능의 동작 방식",
  styles: {
    default: {
      document: { run: { font: FONT, size: 20, color: C.ink }, paragraph: { spacing: { line: 312, after: 120 } } },
    },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 40, bold: true, color: C.ink }, paragraph: { spacing: { after: 160 } } },
      { id: "Eyebrow", name: "Eyebrow", basedOn: "Normal", next: "Normal",
        run: { size: 16, color: C.muted, characterSpacing: 20 }, paragraph: { spacing: { after: 60 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: C.ink },
        paragraph: { spacing: { before: 380, after: 140 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22, bold: true, color: C.accent },
        paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 240 } } } }] },
      { reference: "steps",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: ["상의 색 변경(색상환) 동작 방식 · ", PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 16, color: C.muted }),
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
