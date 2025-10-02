from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "API running. Use POST with JSON body to get metrics."}

@app.post("/")
async def check_latency(req: Request):
    body = await req.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    json_path = Path(__file__).parent.parent / "telemetry.json"
    if not json_path.exists():
        return {"regions": {}, "error": f"JSON not found at {json_path}"}

    df = pd.read_json(json_path)

    expected = {"region", "latency_ms", "uptime_pct"}
    if not expected.issubset(df.columns):
        return {"regions": {}, "error": f"JSON missing required columns. Found: {list(df.columns)}"}

    results = {}
    for region in regions:
        sub = df[df["region"] == region]
        if sub.empty:
            continue
        avg_latency = float(sub["latency_ms"].mean())
        p95_latency = float(np.percentile(sub["latency_ms"], 95))
        avg_uptime = float(sub["uptime_pct"].mean())
        breaches = int((sub["latency_ms"] > threshold).sum())

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    # ✅ Always wrap in "regions"
    return {"regions": results}
