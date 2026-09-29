"""폐기됨 — 3개 스크립트로 분리했다.

얼굴 검출(YuNet)과 확산 생성을 한 프로세스에 같이 넣었더니 AnyDoor venv 의
cv2 4.7.0 에서 YuNet 이 깨졌다 (NaryEltwise shape 불일치). CGI venv 의
cv2 4.11.0 에서는 정상이라, compare_runs.py / rescore.py 를 나눴던 것과
같은 이유로 venv 별로 쪼갰다.

    predict_upper_body.py   1단계  CGI venv    얼굴 검출 + 상반신 크롭 + 예측
    generate_upper_body.py  2단계  AnyDoor venv 실제 합성 (얼굴 검출 없음)
    score_upper_body.py     3단계  CGI venv    SFace 채점 + 전신 결과와 비교

순서대로 실행할 것.
"""
raise SystemExit(
    "이 스크립트는 폐기됐습니다. "
    "predict_upper_body.py -> generate_upper_body.py -> score_upper_body.py "
    "순으로 실행하십시오."
)
