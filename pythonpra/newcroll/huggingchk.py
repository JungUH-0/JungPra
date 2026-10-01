from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="snunlp/KR-FinBert-SC"
)

# 아까 크롤링한 제목 하나로 테스트
result = classifier("삼성전자, CSS 사업팀 인력 60% 재배치…메모리·파운드리로 이동")
print(result)