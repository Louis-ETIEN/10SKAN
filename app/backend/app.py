# main.py

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import requests
import json
from pathlib import Path
import data_extraction


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
HTML_DIR = DOWNLOAD_DIR / "html"
GAAP_DIR = DOWNLOAD_DIR / "gaap"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=TEMPLATES_DIR)

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
app.mount("/downloads/html", StaticFiles(directory=HTML_DIR), name="html")
app.mount("/downloads/gaap", StaticFiles(directory=GAAP_DIR), name="gaap")
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

def get_10k_data(ticker: str, request: Request):

    ticker = ticker.upper()

    ## Retrieve 10k
 
    filepath_10k = HTML_DIR / f"{ticker}_10K.html"

    cik = request.app.state.ticker_to_cik.get(ticker)

    if not cik: 
        return {"error": "Ticker not found"}
    
    filing_url = data_extraction.get_filing_url(cik)

    if not filing_url:
        return {"error": "10-K not found"}

    if not filepath_10k.exists():
        filing_response = requests.get(filing_url, headers=HEADERS_SEC)
        filepath_10k.write_bytes(filing_response.content)

    ## Retrieve gaap data

    filepath_gaap = GAAP_DIR / f"{ticker}_gaap.json"

    if not filepath_gaap.exists():
        gaap = data_extraction.extract_financials(cik)
        print("saving gaap")
        with open(filepath_gaap, "w") as file:
            json.dump(gaap, file, indent=4)

    return {"download_url": filing_url,
            "preview_url": f"/downloads/html/{ticker}_10K.html", 
            "gaap_url": f"downloads/gaap/{ticker}_gaap.json"}

@app.get("/company")
async def company_page(request: Request, ticker: str = Query(None)):
    if not ticker:
        # Redirect to search page if no ticker
        return RedirectResponse(url="/")

    # Get all necessary links
    data = get_10k_data(ticker, request=request)
    if not data:
        return f"No data found for ticker {ticker}", 404

    # Render the Jinja2 template with the links and ticker embedded
    return templates.TemplateResponse(
        "company.html",        # your Jinja2 template
        {
            "request": request,
            "ticker": ticker,
            "preview_url": data['preview_url'],
            "download_url": data['download_url'],
            "gaap_url": data['gaap_url'],  # optional, in case you use it in JS
        }
    )