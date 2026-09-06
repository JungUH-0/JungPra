"""pptxgenjs는 하이퍼링크 run에 u="sng"를 강제로 넣는다.
테마 통일을 위해 밑줄만 제거한다 (색은 이미 명시적으로 지정돼 있어 유지됨)."""
import shutil
import sys
import zipfile

SRC = "food11_presentation.pptx"
TMP = "food11_presentation.tmp.pptx"
TARGET = "ppt/slides/slide2.xml"

zin = zipfile.ZipFile(SRC)
xml = zin.read(TARGET).decode("utf-8")

count = xml.count(' u="sng"')
if count != 1:
    print(f"중단: slide2.xml의 u=\"sng\" 개수가 {count}개 (1개일 때만 안전하게 제거 가능)")
    sys.exit(1)

patched = xml.replace(' u="sng"', "")

with zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = patched.encode("utf-8") if item.filename == TARGET else zin.read(item.filename)
        zout.writestr(item, data)

zin.close()
shutil.move(TMP, SRC)
print("하이퍼링크 밑줄 제거 완료")
