from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException

class PredictRequest(BaseModel):
    landmarks: list[float]     # 손 관절 좌표들
    label_guess: str = ""        # 기본값 있음 = 선택 항목


app = FastAPI()      # FastAPI 앱 객체 생성 - 이게 서버의 본체

@app.get("/")          # "/" 경로로 GET 요청이 오면 아래 함수를 실행해라
def root():
    return {"message": "Hello SignBridge"}

@app.get("/labels/{label_name}")
def get_label(label_name: str):
    return {"label": label_name, "meaning": "자음 또는 모음"}

@app.get("/search")
def search(keyword: str = "", limit: int = 10):
    return {"keyword": keyword, "limit": limit}

@app.post("/echo")
def echo(message: str):
    return {"received": message}

@app.post("/predict")
def predict(req: PredictRequest):
    return {
        "received_count": len(req.landmarks),
        "label_guess": req.label_guess
    }
#1. 응답 상태 코드/에러 처리
@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(status_code=400, detail="item_id는 0 이상이어야 합니다")
    return {"item_id": item_id}

#PUT / DELETE (나머지 HTTP 메서드)
@app.put("/items/{item_id}")     # 수정
def update_item(item_id: int, name: str):
    return {"item_id": item_id, "updated_name": name}

@app.delete("/items/{item_id}")   # 삭제
def delete_item(item_id: int):
    return {"deleted": item_id}

#응답 모델 지정 (response_model)
class ItemResponse(BaseModel):
    id: int
    name: str

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    return {"id": item_id, "name": "테스트"}