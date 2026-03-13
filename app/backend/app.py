# main.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import requests
import json
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS_SEC = {
    "User-Agent": "Louis Etien louis-etien@hotmail.fr"
}
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
HEADERS_YAHOO = {
    "User-Agent": "Mozilla/5.0"
}
US_EXCHANGE = {"NMS", "NYQ", "ASE"}
CACHE_FILE = BASE_DIR / "resources" / "ticker_cache.json"

@asynccontextmanager
async def lifespan(app: FastAPI):


    # ---- startup code ----
    try: 
        response = requests.get(SEC_TICKER_URL, headers=HEADERS_SEC)
        response.raise_for_status()
        data = response.json()

        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)

    app.state.ticker_to_cik = {
        company["ticker"]: str(company["cik_str"]).zfill(10)
        for company in data.values()
    }

    print(f"Loaded {len(app.state.ticker_to_cik)} tickers")

    yield

    # ---- shutdown code ----
    print("Server shutting down")

app = FastAPI(lifespan=lifespan)

app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open(TEMPLATES_DIR / "index.html") as f:
        return f.read()


@app.get("/search")
def search_company(query: str):

    params = {
        "q": query,
        "quotesCount": 50,
        "newsCount": 0
    }

    response = requests.get(YAHOO_SEARCH_URL, params=params, headers=HEADERS_YAHOO)

    if response.status_code != 200:
        return []

    data = response.json()

    results = []

    result_count = 0

    for item in data.get("quotes", []):
        if item.get("quoteType") != "EQUITY":
            continue
        elif item.get("exchange") not in US_EXCHANGE:
            continue
        else:
            result_count += 1
            results.append({
                "symbol": item.get("symbol"),
                "name": item.get("shortname", "")
            })
            if result_count == 10:
                break

    return results

@app.get("/get_10k")
def get_10k(ticker: str, request: Request):

    ticker = ticker.upper()

    filepath = DOWNLOAD_DIR / f"{ticker}_10K.html"

    cik = request.app.state.ticker_to_cik.get(ticker)

    if not cik: 
        return {"error": "Ticker not found"}
    
    submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    r = requests.get(submission_url, headers=HEADERS_SEC)
    data = r.json()
    time.sleep(0.2) # SEC has a 10 requests/sec limit

    filings = data["filings"]["recent"]

    forms = filings["form"]
    accessions = filings["accessionNumber"]
    documents = filings["primaryDocument"]

    accession = None
    document = None

    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accessions[i].replace("-", "")
            document = documents[i]
            break

    if not accession:
        return {"error": "10-K not found"}
    
    cik_no_zero = str(int(cik))

    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession}/{document}"

    filing_response = requests.get(filing_url, headers=HEADERS_SEC)

    if not filepath.exists():
        with open(filepath, "wb") as f:
            filepath.write_bytes(filing_response.content)

    return {"download_url": filing_url,
            "preview_url": f"/downloads/{ticker}_10K.html"}