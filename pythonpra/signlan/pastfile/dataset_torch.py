import os
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

class TorchSignLanguageDataset(Dataset):
    def __init__(self, base_dir):
        self.video_dir = os.path.join(base_dir, "preprocessed_videos")
        # '두려움' 등 폴더 이름들이 곧 정답 라벨(Label)이 됩니다.
        self.classes = sorted(os.listdir(self.video_dir)) 
        self.data_list = []

        for label_idx, class_name in enumerate(self.classes):
            class_path = os.path.join(self.video_dir, class_name)
            if os.path.isdir(class_path):
                # 한 폴더(동영상 1개) 안에 든 프레임 이미지들을 시간순 정렬
                frames = sorted([os.path.join(class_path, f) for f in os.listdir(class_path) if f.endswith('.jpg')])
                # (프레임 리스트, 정답 번호) 형태로 저장
                self.data_list.append((frames, label_idx))

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, idx):
        frames_paths, label = self.data_list[idx]
        sequence_frames = []

        for frame_path in frames_paths:
            # 한글 경로 우회 로드
            with open(frame_path, 'rb') as f:
                file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE) # 흑백 로드
            
            # 0~255인 픽셀값을 0.0~1.0 사이로 정규화 (AI 학습 최적화)
            img = img.astype(np.float32) / 255.0
            # 차원 확장: (224, 224) -> (224, 224, 1)
            img = np.expand_dims(img, axis=-1)
            sequence_frames.append(img)

        # 리스트를 행렬로 결합: (28, 224, 224, 1)
        sequence_tensor = np.array(sequence_frames, dtype=np.float32)
        
        # 🌟 파이토치 핵심: 이미지 채널(Channel) 위치를 앞으로 변경해야 합니다.
        # (Sequence, Height, Width, Channel) -> (Sequence, Channel, Height, Width)
        sequence_tensor = np.transpose(sequence_tensor, (0, 3, 1, 2))

        return torch.tensor(sequence_tensor), torch.tensor(label, dtype=torch.long)

# 테스트 실행 코드
if __name__ == "__main__":
    dataset = TorchSignLanguageDataset(r"D:\JungPra\pythonpra\signlan")
    if len(dataset) > 0:
        dataloader = DataLoader(dataset, batch_size=1, shuffle=False)
        for X, y in dataloader:
            print("🔥 [PyTorch] 입력 데이터 Shape (Batch, Seq, Ch, H, W):", X.shape)
            print("🔥 [PyTorch] 정답 라벨:", y.item())
            break