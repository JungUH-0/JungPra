import torch
import torch.nn as nn

class SignLanguageCNNLSTM(nn.Module):
    def __init__(self, num_classes=1):
        super(SignLanguageCNNLSTM, self).__init__()
        
        # 1. CNN 파트: 정지 프레임 이미지 한 장의 특징을 압축하는 레이어
        self.feature_extractor = nn.Sequential(
            # Input channel=1 (흑백), Output channel=16, 3x3 커널 사용
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # 크기 반토막 (224x224 -> 112x112)
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # 크기 반토막 (112x112 -> 56x56)
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)  # 크기 반토막 (56x56 -> 28x28)
        )
        
        # CNN이 최종적으로 내뱉는 한 프레임당 총 특징 차원 크기 수식 계산
        # 64채널 * 28 * 28 픽셀 = 50,176 차원
        self.cnn_out_dim = 64 * 28 * 28
        
        # 2. LSTM 파트: 압축된 특징들을 시간순(Sequence)으로 읽어 흐름을 파악하는 레이어
        # hidden_size(은닉층 노드 수)는 128개로 설정, 레이어는 2층으로 튼튼하게 쌓습니다.
        self.lstm = nn.LSTM(input_size=self.cnn_out_dim, hidden_size=128, num_layers=2, batch_first=True)
        
        # 3. 최종 출력층 (FC Layer): 최종 계산된 성분을 바탕으로 정답 단어(클래스)를 맞춤
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        # x의 초기 Shape: (Batch, Sequence, Channel, Height, Width) -> [1, 28, 1, 224, 224]
        batch_size, seq_len, ch, h, w = x.size()
        
        # 🌟 핵심: 28장의 프레임을 한 장씩 CNN에 따로 다 먹여야 합니다.
        # 이를 위해시퀀스 축을 배치 축으로 합쳐서 2차원 공간 연산으로 변환합니다.
        # (Batch * Sequence, Channel, Height, Width) -> [28, 1, 224, 224]
        x = x.view(batch_size * seq_len, ch, h, w)
        
        # CNN 통과 -> Shape: [28, 64, 28, 28]
        features = self.feature_extractor(x)
        
        # LSTM에 먹이기 위해 1차원 벡터 형태로 평평하게 펼치기(Flatten) -> Shape: [28, 50176]
        features = features.view(batch_size * seq_len, -1)
        
        # 🌟 핵심: 다시 원상 복구하여 동영상 시퀀스 형태로 맞춰줍니다.
        # Shape: (Batch, Sequence, CNN_Features) -> [1, 28, 50176]
        features = features.view(batch_size, seq_len, -1)
        
        # LSTM 통과 -> out_lstm Shape: [1, 28, 128]
        out_lstm, _ = self.lstm(features)
        
        # 동영상의 맨 마지막 프레임(28번째 프레임)의 결론 정보만 추출합니다.
        # Shape: [1, 128]
        final_frame_feature = out_lstm[:, -1, :]
        
        # 최종 정답 스코어 계산 -> Shape: [1, num_classes] (클래스 개수에 따른 확률점수 출력)
        output = self.fc(final_frame_feature)
        return output

# 모델 검증용 테스트 코드
if __name__ == "__main__":
    # 임의로 아까 성공하신 데이터셋 규격([1, 28, 1, 224, 224]) 가짜 텐서 생성
    mock_input = torch.randn(1, 28, 1, 224, 224)
    
    # 모델 선언 (현재 정답 단어가 1개이므로 num_classes=1)
    model = SignLanguageCNNLSTM(num_classes=1)
    
    # 순전파 가동
    mock_output = model(mock_input)
    
    print("🎯 [성공] 수어 인식 모델 신경망 빌드 완료!")
    print("🎯 모델 최종 출력 결과 차원 구조 (Batch, Classes 스코어):", mock_output.shape)