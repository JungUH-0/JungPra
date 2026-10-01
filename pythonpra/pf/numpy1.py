import numpy as np

# 1차원 배열 생성
arr = np.array([1, 2, 3, 4, 5])

print(arr.shape)   # 배열의 형태(각 차원의 크기)를 튜플로 반환. 1차원이라 원소 개수 (5,) 만 나옴
print(arr.dtype)   # 배열 원소의 자료형. 정수만 넣었으니 int64 (환경에 따라 int32일 수도 있음)
print(arr.ndim)    # 배열의 차원 수(dimension). 1차원 배열이라 1

# 2차원 배열(행렬) 생성
mat = np.array([[1, 2, 3], [4, 5, 6]])

print(mat.shape)   # (행 개수, 열 개수) → 2행 3열이라 (2, 3)
print(mat.ndim)    # 2차원이라 2

print(mat.size)    # 전체 원소 개수 (행 x 열 = 2 x 3 = 6)
print(mat.T)        # 전치행렬 (Transpose) - 행과 열을 바꿈, (2,3) -> (3,2)

mat = np.array([[1, 2, 3],
                 [4, 5, 6],
                 [7, 8, 9]])
print("------------------------")
print(mat[0])       # 인덱스 0번째 행 전체 -> [1 2 3]
print(mat[0, 1])    # 0번째 행, 1번째 열 원소 하나 -> 2
print(mat[:, 2])     # 콜론(:)은 "전체"라는 뜻. 모든 행의 0번째 열 -> [1 4 7]
print(mat[0:, :3])   # 1행부터 끝까지, 열은 0~1번째까지 (2는 포함 안 됨) -> [[4 5] [7 8]]


print("------------------------")
#브로드캐스팅
# 1. 스칼라와의 연산 - 배열 전체에 적용
arr = np.array([1, 2, 3])
print(arr * 2)      # [2 4 6]  각 원소에 2를 곱함
print(arr + 10)      # [11 12 13]  각 원소에 10을 더함

# 2. 같은 shape끼리 연산 - 같은 위치끼리 계산
a = np.array([1, 2, 3])
b = np.array([10, 20, 30])
print(a + b)         # [11 22 33]

# 3. 서로 다른 shape인데도 되는 경우 (진짜 브로드캐스팅)
mat = np.array([[1, 2, 3],
                 [4, 5, 6]])          # shape (2, 3)
row = np.array([100, 200, 300])        # shape (3,)

print(mat.shape)
print(row.shape)
print(mat + row)
# [[101 202 303]
#  [104 205 306]]
# row가 mat의 각 "행"마다 자동으로 반복 적용됨

print("------------------------")
sequence = np.random.rand(10, 3)      # shape (10, 3)
wrist = sequence[0]                     # 손목 좌표라고 가정, shape (3,)

normalized = sequence - wrist           # 모든 프레임에서 손목 좌표를 빼줌 (상대좌표 변환)
print(normalized[4:,2])
print(normalized.shape)                  # (10, 3) 그대로 유지

print("------------------------------------")
flat = np.arange(30)          # 0부터 29까지 1차원 배열, shape (30,)
print(flat.shape)   
print(flat)           # (30,)

seq = flat.reshape(10, 3)      # 같은 데이터를 (10, 3) 형태로 재구성
print(seq.shape)                # (10, 3)
print(seq)
# [[ 0  1  2]
#  [ 3  4  5]
#  [ 6  7  8]
#  ...
#  [27 28 29]]

#-1을 쓰면 numpy가 알아서 계산
seq2 = flat.reshape(10, -1)    # "행은 10개로 하고, 열은 알아서 계산해" -> (10, 3)
seq3 = flat.reshape(-1, 3)     # "열은 3개로 하고, 행은 알아서 계산해" -> (10, 3)

mat = np.array([[1, 2, 3],
                 [4, 5, 6]])    # shape (2, 3)

print(mat.mean())        # 전체 원소 평균: 3.5
print(mat.mean(axis=0))   # 열 방향으로 평균 -> [2.5 3.5 4.5]  (각 열끼리 평균) 1,4  2,5  3,6
print(mat.mean(axis=1))   # 행 방향으로 평균 -> [2. 5.]         (각 행끼리 평균) 1,2,3  4,5,6

seq.mean(axis=0)   # 각 좌표 차원별로, 전체 프레임에 걸친 평균 -> "이 시퀀스의 평균 손 위치"
seq.std(axis=0)     # 각 좌표 차원별로 표준편차 -> "이 시퀀스에서 얼마나 움직였는지"

print("------------------------------------")

#1. 배열 합치기 - concatenate / stack
a= np.array([1,2,3])
b= np.array([4,5,6])
print(np.concatenate([a, b]))
# [1 2 3 4 5 6]  <- 기존 축을 따라 그냥 이어붙임, 차원은 그대로 1차원

print(np.stack([a, b]))
print(np.stack([a, b]).ndim)
# [[1 2 3]
#  [4 5 6]]
# <- 새로운 축을 만들어서 쌓음, 1차원 두 개가 2차원(2,3)이 됨

seq1 = np.random.rand(30, 3)   # 30프레임짜리 시퀀스 1
seq2 = np.random.rand(30, 3)   # 30프레임짜리 시퀀스 2

print(seq1)
print("##############\n")
print(seq2)
dataset = np.stack([seq1, seq2])
print(dataset.shape)   # (2, 30, 3) <- (시퀀스 개수, 프레임, 좌표)
print(dataset)
print(dataset.ndim)

#2. 조건 필터링

arr = np.array([0.1, 0.6, 0.3, 0.9, 0.2])

print(arr > 0.5)                    # [False True False True False] <- True/False 배열
print(arr[arr > 0.5])               # [0.6 0.9]  <- 조건 만족하는 값만 뽑힘

print(np.where(arr > 0.5, 1, 0))    # [0 1 0 1 0]  <- 조건에 따라 값 바꾸기 (True면 1, False면 0)

#3. argmax - 분류 모델에서 필수

output = np.array([0.05, 0.10, 0.75, 0.10])   # 4개 클래스에 대한 모델 확률 출력

print(np.argmax(output))   # 2  <- 가장 큰 값(0.75)의 인덱스

#4. 차원 추가/제거

arr = np.array([1, 2, 3])          # shape (3,)

arr2 = arr[np.newaxis, :]           # shape (1, 3) <- 앞에 차원 하나 추가
arr3 = arr[:, np.newaxis]           # shape (3, 1) <- 뒤에 차원 하나 추가

arr4 = arr2.squeeze()                # shape (3,)  <- 크기 1인 차원 다시 제거

#5. 행렬곱 (딥러닝 연산의 기본)
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6], [7, 8]])


print(a @ b)          # 행렬곱
#결과[0,0] = 1*5 + 2*7 = 5 + 14 = 19
#결과[0,1] = 1*6 + 2*8 = 6 + 16 = 22
#결과[1,0] = 3*5 + 4*7 = 15 + 28 = 43
#결과[1,1] = 3*6 + 4*8 = 18 + 32 = 50
#[[19 22]
#[43 50]]
print(np.dot(a, b))   # 같은 결과
#"행 × 열을 곱하고 다 더하는" 게 행렬곱 하나의 원소를 만드는 방식이에요. 이게 "가중합(weighted sum)"의 정체예요.