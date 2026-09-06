# PPT / 아티팩트 소스

발표 자료와 결과 페이지를 **다시 만들거나 수정할 때** 쓰는 원본 파일들.

| 파일 | 용도 |
|---|---|
| `build.js` | PPT 생성 스크립트 (pptxgenjs). 이걸 고쳐서 다시 빌드한다 |
| `strip_link_underline.py` | 빌드 후처리 — 하이퍼링크 밑줄 제거 |
| `artifact_source.html` | 아티팩트 페이지의 HTML 원본 |

## PPT 다시 빌드하기

```bash
npm install pptxgenjs          # 최초 1회
node build.js                  # food11_presentation.pptx 생성
python strip_link_underline.py # 링크 밑줄 제거 (2번 슬라이드 캐글 출처)
```

빌드 후 검증하려면 pptx 스킬의 validate 스크립트를 쓴다.
한국어 Windows에서는 `PYTHONUTF8=1`을 붙여야 cp949 인코딩 오류가 안 난다.

## 아티팩트 수정하기

`artifact_source.html`을 고친 뒤 Artifact 도구로 아래 URL에 재발행:

```
https://claude.ai/code/artifact/152cfb3a-8394-46b6-9587-843a299ab858
```

Claude Code에서 `url` 파라미터로 이 주소를 넘기면 같은 링크가 유지된다.
단, 재발행 전에 반드시 현재 버전을 먼저 읽어서 그 위에 수정해야 한다
(다른 세션에서 이미 바뀌었을 수 있음).

## build.js 구조

- 상단: 색 팔레트 상수, 헬퍼 함수 (`newSlide`, `card`, `numCircle`, `statBlock` 등)
- 이후: `// ============ N. 이름 ============` 주석으로 구분된 슬라이드 블록 16개
- 슬라이드 순서는 코드에 나온 순서 그대로. 페이지 번호는 `newSlide()`가 자동 부여
- 다크 배경은 `newSlide(true)` — 현재 표지와 결론 두 장뿐

### 주의
- 색상 hex에 `#` 붙이면 파일이 깨진다 (`"16785C"` 형태로)
- 새 슬라이드를 중간에 끼우면 이후 페이지 번호가 자동으로 밀린다
- 스택형 막대 차트에서 `dataLabelPosition: "outEnd"`는 파일을 깨뜨린다
