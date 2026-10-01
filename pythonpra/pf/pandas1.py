import pandas as pd

#1. 핵심 자료구조 두 가지: Series와 DataFrame
# Series - 1차원 , "인덱스가 붙은 리스트" 
s= pd.Series([10,20,30])
print(s)
# 0    10
# 1    20
# 2    30
# dtype: int64
# 왼쪽 숫자(0,1,2)는 자동으로 붙는 "인덱스"

# DataFrame - 2차원, "표" (엑셀 시트 하나)
df = pd.DataFrame({
     "label":["ㄱ","ㄴ","ㄷ"],  #열(column) 하나
     "frame_count": [30,28,32]  #열(column) 둘
})

print(df)
#   label  frame_count
# 0     ㄱ           30
# 1     ㄴ           28
# 2     ㄷ           32
print("#####################")
print(df["label"])
# 0    ㄱ
# 1    ㄴ
# 2    ㄷ
# Name: label, dtype: object

#2. 기본 정보 확인 (데이터 받으면 제일 먼저 하는 것들)


print("HEAD#####################")
print(df.head())    # 위에서 5개 행만 미리보기 (데이터 크면 전체 보기 힘드니까)

print("SHAPE#####################")
print(df.shape)      # (행 개수, 열 개수) -> (3, 2)

print("INFO#####################")
df.info()      # 각 열의 타입, 결측치 여부 등 요약 정보

print("DESCRIBE#####################")
print(df.describe())  # 숫자 열들의 통계 요약 (평균, 표준편차, 최소/최대 등)

print("COLUMNS#####################")
print(df.columns)     # 열 이름들 -> Index(['label', 'frame_count'])

print("DTYPES#####################")
print(df.dtypes)      # 각 열의 자료형



#3. 열/행 선택 (numpy 인덱싱이랑 비슷하면서 다름)

print("#####################")
print(df["label"])                  # 열 하나 선택 -> Series로 반환

print("#####################")
print(df[["label", "frame_count"]]) # 열 여러 개 선택 -> DataFrame으로 반환 (대괄호 두 겹 주의)

print("LOC[i]#####################")
print(df.loc[1])        # 인덱스 이름(label) 기준으로 행 선택

print("ILOC[i]#####################")
print(df.iloc[0])        # 위치(position) 기준으로 행 선택

# 지금은 인덱스가 0,1,2 순서라 둘이 결과 같아 보이는데, 인덱스를 다른 값으로 바꾸면 차이가 드러남


#4. 조건 필터링 (numpy의 arr[arr > 0.5]랑 완전히 같은 패턴)
print("#####################")
print(df[df["frame_count"] > 29])
#   label  frame_count
# 0     ㄱ           30
# 2     ㄷ           32
# frame_count가 29보다 큰 행만 남음



df2 = pd.DataFrame({
    "label": ["ㄱ", "ㄴ", "ㄷ"],
    "frame_count": [30, 28, 32]
}, index=["a", "b", "c"])       # 인덱스를 문자로 지정

print(df2)
#    label  frame_count
# a      ㄱ           30
# b      ㄴ           28
# c      ㄷ           32

print("#####################")
print(df2.loc["a"])     # 인덱스 이름 "a"로 찾음 -> 정상 작동
# label            ㄱ
# frame_count     30

print("#####################")
print(df2.iloc[0])       # 위치 0번째로 찾음 -> 여전히 정상 작동 (a랑 같은 행)
# label            ㄱ
# frame_count     30

print("#####################")
# print(df2.loc[0])     # 에러! 인덱스 이름에 0이 없음 (a,b,c만 있음)

import numpy as np

df3 = pd.DataFrame({
     "label" : ["ㄱ","ㄴ","ㄷ","ㄹ"],
     "frame_count" : [30, None, 32, 25], # 하나 비어있음
     "confidence" : [0.95, 0.88, np.nan, 0.75] #하나 비어있음(np.nan으로 표현)
})
print(df3) 
#   label  frame_count  confidence
# 0     ㄱ         30.0        0.95
# 1     ㄴ          NaN        0.88
# 2     ㄷ         32.0         NaN
# 3     ㄹ         25.0        0.75
# frame_count 정수였지만 None 결측치를 표현할 방법이 없어서 pandas가 자동으로 실수로 잡으면서 변환이 일어남

print("ISNA################")
print(df3.isna())
#    label  frame_count  confidence
# 0  False        False       False
# 1  False         True       False
# 2  False        False        True
# 3  False        False       False
#결측치가 True 로 표현됨 

print("NONTA################")
print(df3.notna())
#    label  fram_count  confidence
# 0   True        True        True
# 1   True       False        True
# 2   True        True       False
# 3   True        True        True
#isna와 반대로 결측치가 False 로 표현

print("ISNA SUM##################")
print(df3.isna().sum()) # 각 열마다 결측치 개수를 셈
# label          0
# frame_count    1
# confidence     1

print("DROPNA################")
print(df3.dropna())
#   label  frame_count  confidence
# 0     ㄱ         30.0        0.95
# 3     ㄹ         25.0        0.75

# 특정 열 기준으로만 검사하고 싶으면
print("#"*20)
print(df3.dropna(subset=["frame_count"]))   # frame_count가 비어있는 행만 제거

print("FILLNA 0###################")
print(df3.fillna(0))
# print(df3.dtypes)

print("FILLNA MEAN#####################") # 그 열의 평균값으로 채움
print(df3["frame_count"].fillna(df3["frame_count"].mean()))
# print(df3["frame_count"].fillna(df3["frame_count"].median()))


#print(df3 is df3.dropna()) ->  False
#df3 원본 주소가 있고 dropna()시 새로운 주소메모리 할당 원본자체를 변경할려면 df3 = df3.dropna()혹은 df3.dropna(inplace=True) 로 수정

df = pd.DataFrame({
    "label": ["ㄱ", "ㄱ", "ㄴ", "ㄴ", "ㄴ", "ㄷ"],
    "frame_count": [30, 32, 28, 25, 27, 40],
    "confidence": [0.95, 0.91, 0.88, 0.75, 0.80, 0.99]
})

print(df)
#   label  frame_count  confidence
# 0     ㄱ           30        0.95
# 1     ㄱ           32        0.91
# 2     ㄴ           28        0.88
# 3     ㄴ           25        0.75
# 4     ㄴ           27        0.80
# 5     ㄷ           40        0.99

print("GROUPBY MEAN#####################")
print(df.groupby("label")["frame_count"].mean())

print("GROUPBY SUM#####################")
print(df.groupby("label")["frame_count"].sum())     # 그룹별 합

print("GROUPBY COUNT#####################")
print(df.groupby("label")["frame_count"].count())    # 그룹별 개수

print("GROUPBY MAX#####################")
print(df.groupby("label")["confidence"].max())        # 그룹별 최댓값

print("GROUPBY MULTI#####################")
print(df.groupby("label")[["frame_count", "confidence"]].mean())
#       frame_count  confidence
# label
# ㄱ           31.0       0.930
# ㄴ           26.666667   0.810
# ㄷ           40.0       0.990

print("GROUPBY AGG#####################")
print(df.groupby("label")["frame_count"].agg(["mean", "std", "count"])) 
#       mean       std  count
# label
# ㄱ    31.0  1.414214      2
# ㄴ    26.666667  1.527525      3
# ㄷ    40.0       NaN      1
#std 표준편차 데이터2개 이상에서 계산 가능

#groupby가 split/apply/combine 순으로 진행

print(df.groupby("label")["label"].count())
# label
# ㄱ    2
# ㄴ    3
# ㄷ    1
# Name: label, dtype: int64
# result1 = df.groupby("label")["label"].count()
# print(result1.name)   # 'label'
# result1 = result1.rename("count")
# result1.name = "count"  
# print(result1.name) # 'count'
# print(df.groupby("label")["label"].count().rename("count")) # 이런 형식으로 result란 변수에 저장 없이 바로 변경가능
# print((df.groupby("label")["label"].count()).name = "count") 이건 불가능함

print(df["label"].value_counts())
# label
# ㄴ    3
# ㄱ    2
# ㄷ    1
# Name: count, dtype: int64



print(df.groupby("label").count())
#        frame_count  confidence
# label                         
# ㄱ                2           2
# ㄴ                3           3
# ㄷ                1           1
# 위에 3개의 차이점들 잘 이해하기 

#DataFrame의 이름을 바꿀 때도 rename 사용가능 
# df_renamed = df.rename(columns={"label": "sign_label"})

df_a = pd.DataFrame({
     "label" :["ㄱ","ㄴ"],
     "frame_count" : [30,28]
})

df_b = pd.DataFrame({
     "label" :["ㄷ","ㄹ"],
     "frame_count" : [32,25]
})

print("CONCAT#########################")
print(pd.concat([df_a, df_b]))

print("CONCAT RESET_INDEX#####################")
print(pd.concat([df_a, df_b], ignore_index=True))

#ignore_index 는 1회성 
result = pd.concat([df_a, df_b], ignore_index=True)
print("IGNORE TEST##############################")
print(result)

df_c = pd.DataFrame({
     "label" :["ㅁ","ㅂ"],
     "frame_count" : [29,40]
})
result = pd.concat([result, df_c])
print("NEWIGNORE TEST##############################")
print(result)

df_d = pd.DataFrame({
     "Label" :["ㅅ","ㅇ"],
     "confidence":[0.99, 0.95]
})

#열의 이름이 같으면 알아서 병합하지만 같지않으면 새로운 열이 생겨서 없는 목록은 NaN으로 표시 오타로 열의 이름이 조금 다르면 아예 새로운 열 추가
result = pd.concat([result, df_d])
print("COLUNM NAME##############################")
print(result)

all_data = []
for file_info in [("파일1", "ㄱ", 30), ("파일2", "ㄴ", 28), ("파일3", "ㄷ", 32)]:
    row = pd.DataFrame({
        "file": [file_info[0]],
        "label": [file_info[1]],
        "frame_count": [file_info[2]]
    })
    all_data.append(row)

print("CONCAT LOOP RESULT#####################")
print(pd.concat(all_data, ignore_index=True))

# 표1: 라벨별 기본 정보
df_label = pd.DataFrame({
    "label": ["ㄱ", "ㄴ", "ㄷ"],
    "category": ["자음", "자음", "자음"]
})

# 표2: 라벨별 통계 정보 (다른 스크립트에서 따로 만들어졌다고 가정)
df_stats = pd.DataFrame({
    "label": ["ㄱ", "ㄴ", "ㄷ"],
    "avg_frame": [31, 26.7, 40],
    "sample_count": [2, 3, 1]
})

print("MERGE#####################")
print(pd.merge(df_label, df_stats))

df_stats2 = pd.DataFrame({
    "label": ["ㄱ", "ㄴ"],          # "ㄷ"이 빠져있음
    "avg_frame": [31, 26.7]
})

print("MERGE INNER (기본값)#####################")
print(pd.merge(df_label, df_stats2, on="label"))

print("MERGE LEFT#####################")
print(pd.merge(df_label, df_stats2, on="label", how="left")) 
#how 옵션 inner 기본 양쪽다 있는것 left 왼쪽표는 남기고 right 오른쪽표는 남기고 outer 양쪽 다 살리지만 없는건 NaN

df = pd.DataFrame({
    "label": ["ㄱ", "ㄴ", "ㄷ"],
    "frame_count": [30, 28, 32],
    "confidence": [0.95, 0.88, 0.99]
})

df.to_csv("signbridge_meta.csv")
# index=False 없이 저장하면
# ,label,frame_count,confidence
# 0,ㄱ,30,0.95
# 1,ㄴ,28,0.88
# 2,ㄷ,32,0.99

df.to_csv("signbridge_meta.csv", index=False)
# index=False로 저장하면 (깔끔함)
# label,frame_count,confidence
# ㄱ,30,0.95
# ㄴ,28,0.88
# ㄷ,32,0.99

loaded_df = pd.read_csv("signbridge_meta.csv")

print("READ_CSV#####################")
print(loaded_df)
print("#####################")
print(loaded_df.dtypes)

#한글 파일 깨질 경우 encoding = "utf-8-sig" 사용 저장시와 불러오기 둘 다 통일 시 좋음
#여러 옵션
pd.read_csv("파일.csv", nrows=5)              # 앞 5줄만 미리 읽기 (큰 파일 확인할 때)
pd.read_csv("파일.csv", usecols=["label", "frame_count"])   # 필요한 열만 선택해서 읽기
pd.read_csv("파일.csv", dtype={"label": "str"})   # 열 타입을 명시적으로 지정