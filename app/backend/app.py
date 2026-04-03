# main.py

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import requests
import json
from pathlib import Path
from financial_data import Financial_data

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
HTML_DIR = DOWNLOAD_DIR / "html"
FINANCIALS_DIR = DOWNLOAD_DIR / "financials"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=TEMPLATES_DIR)

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS_SEC = {
    "User-Agent": "Louis Etien louis.canellou@gmail.fr"
}
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
HEADERS_YAHOO = {
    "User-Agent": "Mozilla/5.0"
}
US_EXCHANGE = {"NMS", "NYQ", "ASE"}
CIK_TICKER_CACHE = BASE_DIR / "resources" / "cik_ticker_cache.json"

@asynccontextmanager
async def lifespan(app: FastAPI):

    try: 
        response = requests.get(SEC_TICKER_URL, headers=HEADERS_SEC)
        response.raise_for_status()
        data = response.json()

        with open(CIK_TICKER_CACHE, "w") as f:
            json.dump(data, f)
    except:
        with open(CIK_TICKER_CACHE, "r") as f:
            data = json.load(f)

    app.state.ticker_to_cik = {
        company["ticker"]: str(company["cik_str"]).zfill(10)
        for company in data.values()
    }

    print(f"Loaded {len(app.state.ticker_to_cik)} tickers")

    yield

app = FastAPI(lifespan=lifespan)

app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")
app.mount("/downloads/html", StaticFiles(directory=HTML_DIR), name="html")
app.mount("/downloads/financials", StaticFiles(directory=FINANCIALS_DIR), name="financials")
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

    try:
        response = requests.get(YAHOO_SEARCH_URL, params=params, headers=HEADERS_YAHOO)
        response.raise_for_status()
        data = response.json()
    except: 
        return []

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

@app.get("/company")
async def company_page(request: Request, ticker: str = Query(None)):
    if not ticker:
        # Redirect to search page if no ticker
        return RedirectResponse(url="/")

    # Get all necessary links

    cik = request.app.state.ticker_to_cik.get(ticker)
    # try:
    data = get_10k_data(ticker, cik)
    # except Exception as e:
    #     return HTTPException(status_code=502, detail=str(e))

    # Render the Jinja2 template with the links and ticker embedded
    return templates.TemplateResponse(
        "company.html",
        {
            "request": request,
            "ticker": ticker,
            "preview_url": data['preview_url'],
            "download_url": data['download_url'],
        }
    )
    
@app.get("/financials")
def financials_page(request: Request, ticker: str):

    json_path = FINANCIALS_DIR / f"{ticker}_financials.json"

    if not json_path.exists():
        return f"No financial data found for {ticker}", 404

    with open(json_path) as f:
        data = json.load(f)

    # years are the keys of the json
    years = [y for y in data.keys() if (y != "market_metrics" and y != "multi_year_metrics")]
    years = sorted(years, reverse=True)[:3]

    return templates.TemplateResponse(
        "financials.html",
        {
            "request": request,
            "ticker": ticker,
            "financials": data,
            "years": years
        }
    )

def get_10k_data(ticker: str, cik: str):

    ticker = ticker.upper()
    filepath_10k = HTML_DIR / f"{ticker}_10K.html"
    filepath_financials = FINANCIALS_DIR / f"{ticker}_financials.json"

    # Get the url of the last 10K filing
    filing_url = Financial_data.get_10K_filing_url(cik)

    # Download the latest 10K if it's not cached
    if not filepath_10k.exists():
        filing_response_10K = requests.get(filing_url, headers=HEADERS_SEC)
        filing_response_10K.raise_for_status()
        filepath_10k.write_bytes(filing_response_10K.content)

    # Fetch and compute the financial data of the company if not cached
    if not filepath_financials.exists():
        financials = Financial_data.from_ticker_cik(ticker, cik, 11)
        financials.save_financials()

    return {"download_url": filing_url,
            "preview_url": f"/downloads/html/{ticker}_10K.html", 
            "financials_url": f"downloads/financials/{ticker}_financials.json"}

if __name__ == "__main__":
    get_10k_data(ticker="AAPL", cik="0000320193")