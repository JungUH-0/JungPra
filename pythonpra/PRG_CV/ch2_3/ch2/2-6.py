import cv2 as cv
import sys

img=cv.imread('girl_laughing.jpg') 
  
if img is None:
    sys.exit('파일을 찾을 수 없습니다.')

cv.rectangle(img,(830,30),(1000,200),(0,0,255),2)	# 직사각형 그리기 파일명,(왼쪽위X,왼쪽위Y),(오른쪽아래X,오른쪽아래Y),(B,G,R),선굵기)
cv.putText(img,'laugh',(830,24),cv.FONT_HERSHEY_SIMPLEX,1,(255,0,0),5)	# 글씨 쓰기 // 파일명,'쓰고싶은 글자',(위치X,위치Y),폰트,폰트크기,(B,G,R),글씨굵기)

cv.imshow('Draw',img)

cv.waitKey()
cv.destroyAllWindows()