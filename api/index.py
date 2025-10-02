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

    # Always resolve CSV path from repo root
    csv_path = Path(__file__).parent.parent / "telemetry.csv"
    if not csv_path.exists():
        return {"error": f"CSV not found at {csv_path}"}

    df = pd.read_csv(csv_path)

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
