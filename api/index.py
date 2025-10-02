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
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "API running. Use POST with JSON body to get metrics."}

@app.post("/")
async def check_latency(req: Request):
    body = await req.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    # Always resolve JSON path from repo root
    json_path = Path(__file__).parent.parent / "telemetry.json"
    if not json_path.exists():
        return {"error": f"JSON not found at {json_path}"}

    # Load JSON into DataFrame
    df = pd.read_json(json_path)

    # Make sure it has the right columns
    expected = {"region", "latency_ms", "uptime"}
    if not expected.issubset(df.columns):
        return {"error": f"JSON missing required columns. Found: {list(df.columns)}"}

    results = {}
    for region in regions:
        sub = df[df["region"] == region]
        if sub.empty:
            continue
        avg_latency = float(sub["latency_ms"].mean())
        p95_latency = float(np.percentile(sub["latency_ms"], 95))
        avg_uptime = float(sub["uptime"].mean())
        breaches = int((sub["latency_ms"] > threshold).sum())

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return results
