
import numpy as np

x = np.random.rand(55)              # shape (55,)

# 가중치(weight)와 편향(bias) - 학습되기 전 랜덤 초기값이라고 가정
# "55차원 입력을 받아서 32차원으로 변환하는 층"
W = np.random.randn(55, 32) * 0.01   # shape (55, 32)
b = np.zeros(32)                      # shape (32,)

# forward pass (순전파) - 이게 nn.Linear(55, 32)가 내부에서 하는 일 그대로
output = x @ W + b
print(output.shape)   # (32,)

def relu(x):
    return np.maximum(0, x)   # 음수는 0으로, 양수는 그대로

x = np.random.rand(55)
W = np.random.randn(55, 32) * 0.01
b = np.zeros(32)

z = x @ W + b        # 선형 변환 (행렬곱 + bias)
a = relu(z)           # 활성화 함수 통과

print(a.shape)   # (32,)

batch_x = np.random.rand(10, 55)     # shape (10, 55) - 샘플 10개, 각각 55차원
W = np.random.randn(55, 32) * 0.01
b = np.zeros(32)

output = batch_x @ W + b
print(output.shape)   # (10, 32) - 샘플 10개가 각각 32차원 결과로


x = np.random.rand(10, 55)             # 배치 10개, 55차원 입력

W1 = np.random.randn(55, 32) * 0.01
b1 = np.zeros(32)
W2 = np.random.randn(32, 10) * 0.01     # 10개 클래스(예: 숫자 0~9) 출력
b2 = np.zeros(10)

h = relu(x @ W1 + b1)      # 1층: (10,55)@(55,32) -> (10,32)
output = h @ W2 + b2         # 2층: (10,32)@(32,10) -> (10,10)

print(output.shape)   # (10, 10) - 샘플 10개, 각각 클래스 10개에 대한 점수

predictions = np.argmax(output, axis=1)   # 각 샘플마다 가장 높은 점수의 클래스
print(predictions.shape)   # (10,) - 샘플 10개에 대한 예측 라벨