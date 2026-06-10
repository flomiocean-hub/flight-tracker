#!/usr/bin/env python3
"""
排程腳本：每日抓機票最低價，追加 price_history，git push。
執行方式：python3 update_flights.py
"""

import json
import subprocess
from datetime import date
from pathlib import Path

# ─── 設定 ────────────────────────────────────────────────────────────────────
FLIGHTS_JSON = Path(__file__).parent / "flights.json"
TODAY = date.today().isoformat()

# ─── 1. 抓機票（替換成真實爬蟲或 API 呼叫） ──────────────────────────────────
def fetch_routes() -> list[dict]:
    """
    回傳當日最新航班列表。
    目前為範例資料，請替換成實際資料來源。
    """
    # TODO: 接真實 API / 爬蟲
    return [
        {
            "from": "TPE", "to": "OKA",
            "date": "2026-07-01",
            "price": 2990,
            "airline": "MM",
            "departure": "07:00",
            "arrival": "10:25",
            "link": "https://www.flypeach.com"
        },
        {
            "from": "TPE", "to": "OKA",
            "date": "2026-07-01",
            "price": 3200,
            "airline": "BR",
            "departure": "08:00",
            "arrival": "11:30",
            "link": "https://www.evaair.com"
        },
    ]

# ─── 2. 讀取既有 JSON ─────────────────────────────────────────────────────────
def load_existing() -> dict:
    if FLIGHTS_JSON.exists():
        return json.loads(FLIGHTS_JSON.read_text())
    return {"updated_at": TODAY, "routes": [], "price_history": []}

# ─── 3. 追加今日最低價（不覆蓋歷史） ─────────────────────────────────────────
def append_price_history(data: dict, routes: list[dict]) -> None:
    min_price = min(r["price"] for r in routes) if routes else None
    if min_price is None:
        return

    history: list[dict] = data.setdefault("price_history", [])

    # 若今天已有紀錄則更新，否則追加
    existing = next((h for h in history if h["date"] == TODAY), None)
    if existing:
        existing["min_price"] = min_price
    else:
        history.append({"date": TODAY, "min_price": min_price})

# ─── 4. 寫回 JSON ─────────────────────────────────────────────────────────────
def save(data: dict) -> None:
    FLIGHTS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"✅ flights.json updated — {TODAY}, min={data['routes'] and min(r['price'] for r in data['routes'])}")

# ─── 5. git commit & push ────────────────────────────────────────────────────
_token_file = Path(__file__).parent / ".github_token"
GITHUB_TOKEN = _token_file.read_text().strip() if _token_file.exists() else ""
GITHUB_REMOTE = f"https://{GITHUB_TOKEN}@github.com/flomiocean-hub/flight-tracker.git"

def git_push() -> None:
    repo = FLIGHTS_JSON.parent
    cmds = [
        ["git", "-C", str(repo), "remote", "set-url", "origin", GITHUB_REMOTE],
        ["git", "-C", str(repo), "config", "user.email", "paleblue.ml@gmail.com"],
        ["git", "-C", str(repo), "config", "user.name", "Marco Liu"],
        ["git", "-C", str(repo), "add", "flights.json"],
        ["git", "-C", str(repo), "commit", "-m", f"chore: update flights {TODAY}"],
        ["git", "-C", str(repo), "push", "origin", "main", "--set-upstream"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # "nothing to commit" は正常
            if "nothing to commit" in result.stdout + result.stderr:
                print("ℹ️  nothing to commit")
                return
            print(f"⚠️  {' '.join(cmd)}\n{result.stderr}")
            return
    print("🚀 pushed to origin/main")

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    routes = fetch_routes()
    data = load_existing()
    data["updated_at"] = TODAY
    data["routes"] = routes
    append_price_history(data, routes)
    save(data)
    git_push()
