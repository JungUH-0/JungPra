# 정규화 하기
import numpy as np
import os
import glob

npy_dir = r"D:\JungPra\pythonpra\signlan\npy_output"
files   = sorted(glob.glob(os.path.join(npy_dir, "*.npy")))
print(f"총 {len(files)}개 정규화 시작...")

for i, f in enumerate(files):
    data = np.load(f)
    data[:, 0::2] = data[:, 0::2] / 1920.0  # x 정규화
    data[:, 1::2] = data[:, 1::2] / 1080.0  # y 정규화
    data = np.clip(data, 0.0, 1.0)
    np.save(f, data)
    if (i+1) % 1000 == 0:
        print(f"  {i+1}/{len(files)} 완료...")

print("✅ 정규화 완료!")

# 확인
sample = np.load(files[0])
print(f"확인 - min: {sample.min():.3f}, max: {sample.max():.3f}")