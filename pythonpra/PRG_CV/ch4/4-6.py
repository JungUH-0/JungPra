import skimage
from skimage import graph
import numpy as np
import cv2 as cv
import time

# coffee=skimage.data.coffee()

# start=time.time()
# slic=skimage.segmentation.slic(coffee,compactness=20,n_segments=600,start_label=1)
# g=skimage.future.graph.rag_mean_color(coffee,slic,mode='similarity') 
# ncut=skimage.future.graph.cut_normalized(slic,g)	# 정규화 절단
# print(coffee.shape,' Coffee 영상을 분할하는데 ',time.time()-start,'초 소요')

# marking=skimage.segmentation.mark_boundaries(coffee,ncut)
# ncut_coffee=np.uint8(marking*255.0)

# cv.imshow('Normalized cut',cv.cvtColor(ncut_coffee,cv.COLOR_RGB2BGR))  

# cv.waitKey()
# cv.destroyAllWindows()

coffee = skimage.data.coffee()

start = time.time()

# 1. SLIC 분할
slic = skimage.segmentation.slic(coffee, compactness=20, n_segments=600, start_label=1)

# 2. RAG 생성 (skimage.future.graph -> graph.rag_mean_color로 변경)
g = graph.rag_mean_color(coffee, slic, mode='similarity') 

# 3. 정규화 절단 (skimage.future.graph -> graph.cut_normalized로 변경)
ncut = graph.cut_normalized(slic, g) 

print(coffee.shape, ' Coffee 영상을 분할하는데 ', time.time()-start, '초 소요')

# 4. 경계선 표시
marking = skimage.segmentation.mark_boundaries(coffee, ncut)
ncut_coffee = np.uint8(marking * 255.0)

# 5. 결과 출력 (RGB -> BGR 변환)
cv.imshow('Normalized cut', cv.cvtColor(ncut_coffee, cv.COLOR_RGB2BGR))  

cv.waitKey()
cv.destroyAllWindows()