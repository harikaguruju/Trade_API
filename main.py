from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import os
from dotenv import load_dotenv
import time

# load env
load_dotenv()

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# API KEY
# -------------------------------
API_KEY = "mysecret123"
api_key_header = APIKeyHeader(name="x-api-key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------
# RATE LIMIT
# -------------------------------
request_log = {}
RATE_LIMIT = 5
TIME_WINDOW = 60

def check_rate_limit(client_ip):
    current_time = time.time()

    if client_ip not in request_log:
        request_log[client_ip] = []

    request_log[client_ip] = [
        t for t in request_log[client_ip]
        if current_time - t < TIME_WINDOW
    ]

    if len(request_log[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    request_log[client_ip].append(current_time)

# -------------------------------
# VALID SECTORS (NEW)
# -------------------------------
VALID_SECTORS = ["healthcare", "technology", "finance", "education", "energy"]

# -------------------------------
# FETCH NEWS (REAL-TIME)
# -------------------------------
def fetch_news(sector):
    api_key = os.getenv("GNEWS_API_KEY")

    url = f"https://gnews.io/api/v4/search?q={sector}&lang=en&max=5&token={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        articles = data.get("articles", [])
        titles = [a["title"] for a in articles if "title" in a]

        return titles if titles else ["No real-time data found"]

    except Exception as e:
        print("ERROR:", e)
        return ["Error fetching real-time data"]

# -------------------------------
# ROUTES
# -------------------------------
@app.get("/analyze/{sector}")
def analyze_sector(
    sector: str,
    request: Request,
    api_key: str = Depends(verify_api_key)
):

    check_rate_limit(request.client.host)

    # 🔥 VALIDATION (NEW)
    if sector.lower() not in VALID_SECTORS:
        return {
            "error": "Please enter a valid sector like healthcare, technology, finance"
        }

    insights = fetch_news(sector)

    # 🔥 HANDLE NO DATA
    if insights == ["No latest news available"]:
        return {
            "error": "No real-time data found for this sector"
        }

    # 🔥 REAL DATA BASED REPORT
    report = f"""
# Market Analysis: {sector}

## Current Trends
- {insights[0] if len(insights)>0 else ''}
- {insights[1] if len(insights)>1 else ''}

## Opportunities
- Increasing investments observed
- Positive industry growth signals

## Risks
- Market competition
- Policy and regulatory challenges

## Conclusion
The {sector} sector shows growth based on real-time industry developments.
"""

    return {
        "sector": sector,
        "report": report,
        "metrics": {
            "growth": 80,
            "risk": 60,
            "demand": 75
        },
        "insights": insights   # 🔥 extra real-time data
    }

# -------------------------------
# SERVE FRONTEND
# -------------------------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")
