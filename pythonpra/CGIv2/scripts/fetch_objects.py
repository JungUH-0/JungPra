"""2안 물건 사진 — Unsplash 에서 **검색과 받기를 나눠** 가져온다. 모델 없음.

    search  후보 목록만 만든다. 이미지는 받지 않는다 — 크기는 HEAD 요청으로만 잰다.
            → <out>/_candidates.json
    get     사람이 고른 후보만 받는다 → <out>/<이름>.jpg + _credits.json

1안 수집(AnyDoor/data_test/fetch_unsplash.py)과 같은 경로다. API 키 없이 napi
검색이 되고, 파이썬 urllib 는 401 을 받아 curl 을 쓴다. 라이선스는 Unsplash
License — 무료 사용·변형·상업 이용 허용. **Unsplash+ (유료) 사진은 뺀다.**

사용:
    python scripts/fetch_objects.py search
    python scripts/fetch_objects.py get A01=<id> C01=<id> ...
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

NAPI = "https://unsplash.com/napi/search/photos"
WIDTH = 1200          # 받는 폭. 원본은 수십 MB 인 경우가 있다

#: (종류, 검색어, 방향) — 단색 배경 제품 사진을 노린다 (마스크가 깨끗하게 나온다)
QUERIES = [
    ("watch", "wristwatch isolated white background", "squarish"),
    ("watch", "analog watch product photo white background", "squarish"),
    ("car", "car isolated white background", "landscape"),
    ("car", "car studio side view white background", "landscape"),
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def curl(args: list[str]) -> bytes:
    r = subprocess.run(["curl", "-sfL", "--max-time", "60", *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl exit {r.returncode}")
    return r.stdout


def sized_url(raw: str) -> str:
    return f"{raw}{'&' if '?' in raw else '?'}w={WIDTH}&q=85&fm=jpg"


def head_size(url: str) -> int | None:
    """받지 않고 크기만 — HEAD 의 Content-Length."""
    try:
        h = curl(["-I", url]).decode("latin-1").lower()
    except RuntimeError:
        return None
    sizes = [int(l.split(":", 1)[1]) for l in h.splitlines() if l.startswith("content-length:")]
    return sizes[-1] if sizes else None


def search(out: Path, per_query: int) -> int:
    rows, seen = [], set()
    for kind, term, orient in QUERIES:
        q = urllib.parse.urlencode({"query": term, "per_page": str(per_query),
                                    "orientation": orient})
        try:
            res = json.loads(curl([f"{NAPI}?{q}"])).get("results", [])
        except Exception as e:
            print(f"[{kind}] '{term}' 검색 실패 {type(e).__name__}")
            continue
        for r in res:
            if r["id"] in seen or r.get("premium") or r.get("plus"):
                continue
            seen.add(r["id"])
            url = sized_url(r["urls"]["raw"])
            rows.append({
                "kind": kind, "query": term, "id": r["id"],
                "w": r["width"], "h": r["height"],
                "desc": (r.get("alt_description") or "")[:80],
                "author": r["user"].get("name", "?"), "link": r["links"]["html"],
                "download": url, "bytes": head_size(url),
            })
            time.sleep(0.2)
    out.mkdir(parents=True, exist_ok=True)
    (out / "_candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    for kind in ("watch", "car"):
        print(f"\n=== {kind} ===")
        for r in (x for x in rows if x["kind"] == kind):
            kb = f"{r['bytes'] / 1024:5.0f}KB" if r["bytes"] else "   ?KB"
            print(f"{r['id']:12s} {r['w']:>5}x{r['h']:<5} {kb}  {r['desc']}")
    print(f"\n후보 {len(rows)}장 → {out / '_candidates.json'}  (이미지는 아직 받지 않음)")
    return 0


def get(out: Path, picks: list[str]) -> int:
    cands = {r["id"]: r for r in json.loads((out / "_candidates.json").read_text(encoding="utf-8"))}
    cred_f = out / "_credits.json"
    credits = json.loads(cred_f.read_text(encoding="utf-8")) if cred_f.exists() else []
    for p in picks:
        name, cid = p.split("=", 1)
        r = cands[cid]
        path = out / f"{name}.jpg"
        path.write_bytes(curl([r["download"]]))
        credits = [c for c in credits if c["file"] != path.name] + [{"file": path.name, **r}]
        print(f"{path.name:40s} {path.stat().st_size / 1024:6.0f}KB  {r['desc']}  — {r['author']}")
        time.sleep(0.3)
    cred_f.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n출처: {cred_f}")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "get"])
    ap.add_argument("picks", nargs="*", help="get: 이름=id (예: A01_watch-silver=abc123)")
    ap.add_argument("--out", default=str(root / "work" / "plan2" / "raw"))
    ap.add_argument("--per-query", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    return search(out, a.per_query) if a.cmd == "search" else get(out, a.picks)


if __name__ == "__main__":
    raise SystemExit(main())
