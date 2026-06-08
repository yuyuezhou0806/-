"""
Random Median Generator - Backend Server
Serves the demo page + visit tracking (PV/UV)
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Random Median Generator")

DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
STATS_FILE = DATA_DIR / "visit_stats.json"
HTML_FILE = DATA_DIR / "random_median_demo.html"


def load_stats() -> dict:
    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"pv": 0, "uv": 0, "visitors": {}, "daily": {}}


def save_stats(stats: dict):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def get_client_id(request: Request) -> str:
    """Generate anonymous visitor ID from IP + UA"""
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    ua = request.headers.get("user-agent", "")
    raw = f"{ip}|{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@app.get("/api/visit")
async def record_visit(request: Request):
    stats = load_stats()
    client_id = get_client_id(request)
    today = datetime.now().strftime("%Y-%m-%d")

    # PV always +1
    stats["pv"] += 1

    # UV: check if new visitor today
    if client_id not in stats.get("visitors", {}):
        stats["uv"] += 1
        if "visitors" not in stats:
            stats["visitors"] = {}
        stats["visitors"][client_id] = {"first_seen": today, "visits": 1}
    else:
        stats["visitors"][client_id]["visits"] += 1
        stats["visitors"][client_id]["last_seen"] = today

    # Daily stats
    if "daily" not in stats:
        stats["daily"] = {}
    if today not in stats["daily"]:
        stats["daily"][today] = {"pv": 0, "uv": set()}
    stats["daily"][today]["pv"] += 1
    stats["daily"][today]["uv"].add(client_id)

    save_stats(stats)

    # Return daily UV count (convert set to count for response)
    daily_data = {}
    for d, v in stats.get("daily", {}).items():
        daily_data[d] = {"pv": v["pv"], "uv": len(v["uv"]) if isinstance(v.get("uv"), set) else v.get("uv", 0)}

    return {
        "pv": stats["pv"],
        "uv": stats["uv"],
        "today_pv": daily_data.get(today, {}).get("pv", 0),
        "today_uv": daily_data.get(today, {}).get("uv", 0),
        "daily": daily_data,
    }


@app.get("/api/stats")
async def get_stats():
    stats = load_stats()
    daily_data = {}
    for d, v in stats.get("daily", {}).items():
        daily_data[d] = {"pv": v["pv"], "uv": len(v["uv"]) if isinstance(v.get("uv"), set) else v.get("uv", 0)}

    return {
        "pv": stats["pv"],
        "uv": stats["uv"],
        "daily": daily_data,
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    if HTML_FILE.exists():
        return HTML_FILE.read_text(encoding="utf-8")
    return "<h1>Demo page not found</h1>"


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
