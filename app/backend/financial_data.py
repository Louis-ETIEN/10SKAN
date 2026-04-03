from schema import SCHEMA, SCHEMA_MM, SCHEMA_MYM
from tag_map import TAG_MAP
import requests
import yfinance as yf
import time
from copy import deepcopy
import json
from datetime import datetime
from pathlib import Path

HEADERS_SEC = {
    "User-Agent": "Louis Etien louis-etien@hotmail.fr"
}

BASE_DIR = Path(__file__).resolve().parent.parent
FINANCIALS_DIR = BASE_DIR / "downloads" / "financials"

class FilingNotFoundError(Exception):
    pass

class ExternalAPIError(Exception):
    pass

class Financial_data:
    def __init__(self, ticker, cik, n_years):
        self.n_years = n_years
        self.years = []
        self.ticker = ticker
        self.cik = cik
        self.financials = {}

    @classmethod
    def from_ticker_cik(cls, ticker, cik, n_years):
        finances = Financial_data(ticker, cik, n_years)
        facts = finances._get_facts()
        finances._get_years(facts)
        finances._build_template()
        finances._extract_finances(facts)
        finances._compute_backup_metrics()
        #finances._compute_ROIC2(facts)
        finances._compute_derived_metrics()
        finances._fetch_market_metrics()
        finances._compute_multi_year_metrics()
        return finances
    
    def print_financials(self):
        print(json.dumps(self.financials, indent=4))

    def save_financials(self):
        filepath = FINANCIALS_DIR / f"{self.ticker}_financials.json"
        with open(filepath, "w") as file:
            json.dump(self.financials, file, indent=4)

    def _get_facts(self):

        cik = self.cik.zfill(10)

        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

        response = requests.get(url, headers=HEADERS_SEC)

        response.raise_for_status()

        return response.json()
    
    def _get_years(self, facts):

        try:
            years = set()

            assets_entries = facts["facts"]["us-gaap"]["Assets"]["units"]["USD"]

            entries = [e for e in assets_entries if e.get("form") == "10-K"]

            for e in entries:
                years.add(fiscal_year(e["end"]))

            years = list(years) 

            years.sort(reverse=True)

            self.years = years[:self.n_years]
    
        except Exception as e:
            raise KeyError(e) from e
        
    def _build_template(self):
        # Initialise a metric dictionary for every year according to the SHCEMA template
        self.financials = {year: deepcopy(SCHEMA) for year in self.years}

        # Initialise two further dictionaries for multi year metrics and instant metrics
        self.financials["market_metrics"] = deepcopy(SCHEMA_MM)
        self.financials["multi_year_metrics"] = deepcopy(SCHEMA_MYM)
        
    def _extract_finances(self, facts):
        # Fill the yearly dictionaries
        for section in TAG_MAP:
            for metric in TAG_MAP[section]:
                self._extract_metric(facts, section, metric)
    
    def _extract_metric(self, facts, section, metric):
        tags = TAG_MAP[section][metric]
        metric_years = self.years.copy()  ## We need to find the metric for each year
        #print(metric + ":")
        
        for tag in tags:  ## Each metric can be reported under different tags by the company. The tag may be different from one year to another
            #print("    " + tag + ":" + f" ({len(metric_years)} years remaing)")
            if not metric_years:  ## Stop if we found the metric for all years
                return

            try:
                ## Shares must be accessed with unit "shares"
                if metric == "weighted_avg_shares_diluted":
                    unit = "shares"
                ## All other metrics with unit "USD"
                else: 
                    unit = "USD"

                # For metrics in the income and cashflow statements, we have a start and an end data, 
                # so we can double check that the data is for the full year. Sometimes quaterly data is 
                # misleadingly reported under "10-K" without indication other than those dates
                if section in ("income_statement", "cashflow_statement"):
                    entries = facts["facts"]["us-gaap"][tag]["units"][unit]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and "start" in e and "end" in e and \
                        is_full_year(e["start"], e["end"]) and year in metric_years:
                            self.financials[year][section][metric] = e.get("val")
                            metric_years.remove(year)  # We found the metric for that year, we can stop looking for it
                            #print(f"        found year {year}")
                            if not metric_years: 
                                return # Found the metric for all years
                            
                # For balance sheet metrics, the start data is not provided, so we cannot (and don't need)
                # to double check
                else:
                    entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and year in metric_years:
                            self.financials[year][section][metric] = e.get("val")
                            metric_years.remove(year)
                            #print(f"        found year {year}")
                            if not metric_years: 
                                return

            except KeyError:
                continue
        
    def _compute_backup_metrics(self):

        for year in self.years:
            result = self.financials[year]
            if result["cashflow_statement"]["operating_cash_flow"] and \
            result["cashflow_statement"]["capex"]:

                ocf = result["cashflow_statement"]["operating_cash_flow"]
                capex = result["cashflow_statement"]["capex"]

                result["cashflow_statement"]["free_cash_flow"] = ocf - abs(capex)
            
            if not result["income_statement"]["gross_profit"] and result["income_statement"]["revenue"] and result["income_statement"]["cost_of_revenue"]:
                result["income_statement"]["gross_profit"] = result["income_statement"]["revenue"] - result["income_statement"]["cost_of_revenue"]
            
            if not result["balance_sheet"]["shareholders_equity"] and result["balance_sheet"]["total_assets"] and result["balance_sheet"]["total_liabilities"]:
                result["balance_sheet"]["shareholders_equity"] = result["balance_sheet"]["total_assets"] - result["balance_sheet"]["total_liabilities"]

            if not result["balance_sheet"]["total_liabilities"] and result["balance_sheet"]["total_assets"] and result["balance_sheet"]["shareholders_equity"]:
                result["balance_sheet"]["total_liabilities"] = result["balance_sheet"]["total_assets"] - result["balance_sheet"]["shareholders_equity"]


    
    def _compute_derived_metrics(self):
        for year in self.years:
            result = self.financials[year]
            is_ = result["income_statement"]
            bs = result["balance_sheet"]
            cf = result["cashflow_statement"]
            dm = result["derived_metrics"]

            revenue = is_["revenue"]
            gross_profit = is_["gross_profit"]
            operating_income = is_["operating_income"]
            net_income = is_["net_income"]
            weighted_avg_shares_diluted = is_["weighted_avg_shares_diluted"]

            total_assets = bs["total_assets"]
            equity = bs["shareholders_equity"]

            operating_cash_flow = cf["operating_cash_flow"]
            capex = cf["capex"]
            free_cash_flow = cf["free_cash_flow"]

            # Profitability margins
            if revenue and revenue != 0:
                if gross_profit:
                    dm["gross_margin"] = gross_profit / revenue
                if operating_income :
                    dm["operating_margin"] = operating_income / revenue
                if net_income:
                    dm["net_margin"] = net_income / revenue
                if free_cash_flow:
                    dm["fcf_margin"] = free_cash_flow / revenue

            # per-share
            if weighted_avg_shares_diluted and weighted_avg_shares_diluted != 0:
                if net_income:
                    dm["diluted_eps"] = net_income / weighted_avg_shares_diluted
                if free_cash_flow:
                    dm["diluted_fcf_per_share"] = free_cash_flow / weighted_avg_shares_diluted

            # Returns
            if net_income and total_assets and total_assets != 0:
                dm["return_on_assets"] = net_income / total_assets
            if net_income and equity and equity != 0:
                dm["return_on_equity"] = net_income / equity

            # Efficiency
            if revenue and total_assets and total_assets != 0:
                dm["asset_turnover"] = revenue / total_assets

            # Cash metrics
            if operating_cash_flow and net_income and net_income != 0:
                dm["cash_conversion"] = operating_cash_flow / net_income
            if capex and revenue and revenue !=0:
                dm["capex_ratio"] = capex / revenue

    def _compute_ROIC(self, facts):
        # retrieve the tax rate
        tax_rate_years = self.years.copy()
        for tag in TAG_MAP["income_statement"]["tax_rate"]:
            try: 
                entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                for e in entries:
                    year = fiscal_year(e.get("end", ""))
                    if e["form"] == "10-K" and year in tax_rate_years:
                        self.financials[year]["income_statement"]["tax_rate"] = e.get("val")
                        tax_rate_years.remove(year)
                        if not tax_rate_years: 
                            break
            except:
                continue

        if tax_rate_years:
            tax_expense_years = tax_rate_years.copy()
            pretax_years = tax_rate_years.copy()
            for tag in TAG_MAP["income_statement"]["income_tax_expense"]:
                try:
                    entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and year in tax_expense_years:
                            self.financials[year]["income_statement"]["income_tax_expense"] = e.get("val")
                            tax_expense_years.remove(year)
                            if not tax_expense_years:
                                break
                except:
                    continue
            for tag in TAG_MAP["income_statement"]["pretax_income"]:
                try:
                    entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and year in pretax_years:
                            self.financials[year]["income_statement"]["pretax_income"] = e.get("val")
                            pretax_years.remove(year)
                            if not pretax_years:
                                break
                except:
                    continue

        for year in self.years:
            if self.financials[year]["income_statement"]["tax_rate"] == None:
                income_tax_expense = self.financials[year]["income_statement"]["income_tax_expense"]
                pretax_income = self.financials[year]["income_statement"]["pretax_income"]
                if income_tax_expense != None and income_tax_expense != 0 and \
                        pretax_income != None and pretax_income > 0:
                    
                    self.financials[year]["income_statement"]["tax_rate"] = round(income_tax_expense / pretax_income, 2)

            if self.financials[year]["income_statement"]["tax_rate"] == None:
                self.financials[year]["income_statement"]["tax_rate"] = 0.21
                    
        # retrieve the Debt
        debt_years = self.years.copy()
        for tag in TAG_MAP["balance_sheet"]["debt"]:
            print(tag)
            try: 
                entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                for e in entries:
                    print(json.dumps(e, indent=4))
                    year = fiscal_year(e.get("end", ""))
                    if e["form"] == "10-K" and year in debt_years:
                        self.financials[year]["balance_sheet"]["debt"] = e.get("val")
                        debt_years.remove(year)
                        if not debt_years: 
                            break
            except:
                continue

        # fallback: add long-term and short-term debt

        if debt_years:
            debt_current_years = debt_years.copy()
            debt_noncurrent_years = debt_years.copy()
            for tag in TAG_MAP["balance_sheet"]["debt_current"]:
                try:
                    entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and year in debt_current_years:
                            self.financials[year]["balance_sheet"]["debt_current"] = e.get("val")
                            debt_current_years.remove(year)
                            if not debt_current_years:
                                break
                except:
                    continue

            for tag in TAG_MAP["balance_sheet"]["debt_noncurrent"]:
                try:
                    entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
                    for e in entries:
                        year = fiscal_year(e.get("end", ""))
                        if e["form"] == "10-K" and year in debt_noncurrent_years:
                            self.financials[year]["balance_sheet"]["debt_noncurrent"] = e.get("val")
                            debt_noncurrent_years.remove(year)
                            if not debt_noncurrent_years:
                                break
                except:
                    continue

        for year in self.years:
            if self.financials[year]["balance_sheet"]["debt"] == None:
                debt_current = self.financials[year]["balance_sheet"]["debt_current"]
                debt_noncurrent = self.financials[year]["balance_sheet"]["debt_noncurrent"]
                if debt_current != None and debt_noncurrent != None:
                    self.financials[year]["balance_sheet"]["debt"] = debt_current + debt_noncurrent

        # Compute the ROIC for each year
            
        for year in self.years[:-2]:
            tax_rate = self.financials[year]["income_statement"]["tax_rate"]
            operating_income = self.financials[year]["income_statement"]["operating_income"]
            shareholders_equity_t1 = self.financials[str(int(year) - 1)]["balance_sheet"]["shareholders_equity"]
            debt_t1 = self.financials[str(int(year) - 1)]["balance_sheet"]["debt"]
            cash_t1 = self.financials[str(int(year) - 1)]["balance_sheet"]["cash"]
            shareholders_equity_t2 = self.financials[year]["balance_sheet"]["shareholders_equity"]
            debt_t2 = self.financials[year]["balance_sheet"]["debt"]
            cash_t2 = self.financials[year]["balance_sheet"]["cash"]

            #if tax_rate and operating_income and shareholders_equity and debt and cash: 
            self.financials[year]["derived_metrics"]["return_on_invested_capital"] = round((1 - tax_rate) * operating_income / ((shareholders_equity_t1 + debt_t1 - cash_t1) + (shareholders_equity_t2 + debt_t2 - cash_t2)) * 2, 2)

    def _compute_ROIC2(self, facts):
        return

    def _fetch_market_metrics(self):

        stock = yf.Ticker(self.ticker)
        info = stock.info

        revenue = self.financials[self.years[0]]["income_statement"]["revenue"]
        fcf = self.financials[self.years[0]]["cashflow_statement"]["free_cash_flow"]

        mm = self.financials["market_metrics"]

        mm["share_price"] = info.get("currentPrice")
        mm["shares_outstanding"] = info.get("sharesOutstanding")
        mm["market_cap"] = info.get("marketCap")
        mm["enterprise_value"] = info.get("enterpriseValue")

        mm["pe_ratio"] = info.get("trailingPE")
        mm["price_to_sales"] = info.get("priceToSalesTrailing12Months")
        mm["price_to_book"] = info.get("priceToBook")

        ev = mm["enterprise_value"]
        market_cap = mm["market_cap"]

        if ev and revenue:
            mm["ev_to_revenue"] = ev / revenue

        if ev and fcf:
            mm["ev_to_fcf"] = ev / fcf

        if market_cap and fcf:
            mm["fcf_yield"] = fcf / market_cap
        
    def _compute_multi_year_metrics(self):


        mym = self.financials["multi_year_metrics"]
        n = len(self.years)

        def get(path, year):
            try:
                v = self.financials[year]
                for p in path:
                    v = v[p]
                return v
            except:
                return None

        def compute_if_valid(metric_key, horizon, start_val, end_val):
            if start_val and end_val and start_val > 0 and end_val > 0:
                mym[metric_key][f"{horizon}y"] = compute_cagr(start_val, end_val, horizon)

        # Revenue CAGR

        if n >= 4:
            start = get(["income_statement", "revenue"], self.years[3])
            end = get(["income_statement", "revenue"], self.years[0])
            compute_if_valid("revenue_cagr", 3, start, end)

        if n >= 6:
            start = get(["income_statement", "revenue"], self.years[5])
            end = get(["income_statement", "revenue"], self.years[0])
            compute_if_valid("revenue_cagr", 5, start, end)

        if n >= 11:
            start = get(["income_statement", "revenue"], self.years[10])
            end = get(["income_statement", "revenue"], self.years[0])
            compute_if_valid("revenue_cagr", 10, start, end)

        # FCF CAGR

        if n >= 4:
            start = get(["cashflow_statement", "free_cash_flow"], self.years[3])
            end = get(["cashflow_statement", "free_cash_flow"], self.years[0])
            compute_if_valid("fcf_cagr", 3, start, end)

        if n >= 6:
            start = get(["cashflow_statement", "free_cash_flow"], self.years[5])
            end = get(["cashflow_statement", "free_cash_flow"], self.years[0])
            compute_if_valid("fcf_cagr", 5, start, end)

        # Average ROE

        if n >= 5:
            vals = []
            for i in range(5):
                v = get(["derived_metrics", "return_on_equity"], self.years[i])
                if v:
                    vals.append(v)
            if len(vals) == 5:
                mym["avg_roe"]["5y"] = sum(vals) / 5

        if n >= 10:
            vals = []
            for i in range(10):
                v = get(["derived_metrics", "return_on_equity"], self.years[i])
                if v:
                    vals.append(v)
            if len(vals) == 10:
                mym["avg_roe"]["10y"] = sum(vals) / 10

        # Operating Margin Change

        if n >= 4:
            start = get(["derived_metrics", "operating_margin"], self.years[3])
            end = get(["derived_metrics", "operating_margin"], self.years[0])
            if start is not None and end is not None:
                mym["operating_margin_change"]["3y"] = end - start

        # Share Count Change: To implement by adding shares outstanding to income statement

        if n >= 4:
            start = get(["market_metrics", "shares_outstanding"], None)
            end = get(["market_metrics", "shares_outstanding"], None)

        if n >= 4:
            start = get(["income_statement", "shares_outstanding"], self.years[3])
            end = get(["income_statement", "shares_outstanding"], self.years[0])
            if start and end and start > 0:
                mym["share_count_change"]["3y"] = (end / start) - 1

        if n >= 6:
            start = get(["income_statement", "shares_outstanding"], self.years[5])
            end = get(["income_statement", "shares_outstanding"], self.years[0])
            if start and end and start > 0:
                mym["share_count_change"]["5y"] = (end / start) - 1

        # Revenue Volatility (std dev of growth rates)

        if n >= 11:

            growth_rates = []

            for i in range(10):
                r0 = get(["income_statement", "revenue"], self.years[i])
                r1 = get(["income_statement", "revenue"], self.years[i + 1])

                if r0 and r1 and r1 > 0:
                    growth_rates.append((r0 / r1) - 1)

            if len(growth_rates) == 10:

                mean = sum(growth_rates) / 10
                variance = sum((g - mean) ** 2 for g in growth_rates) / 10
                mym["revenue_volatility"]["10y"] = variance ** 0.5

    @staticmethod
    def get_10K_filing_url(cik):
        submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            response = requests.get(submission_url, headers=HEADERS_SEC)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ExternalAPIError(f"Failed to retrieve filing url from the SEC: {e}") from e

        data = response.json()
        time.sleep(0.1) # SEC has a 10 requests/sec limit

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
            raise FilingNotFoundError("No 10-K was found in the SEC filings.")
        
        cik_no_zero = str(int(cik))

        return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession}/{document}"

def fiscal_year(end):

    d = datetime.strptime(end, "%Y-%m-%d")

    # January fiscal year endings belong to previous FY
    if d.month <= 2:
        return str(d.year - 1)
    return str(d.year)
    
def is_full_year(start, end):
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    days = (end - start).days

    return 350 <= days <= 380

def compute_cagr(valuet0, valuet1, deltat):
    return ((valuet1 / valuet0) ** (1 / deltat))  - 1
    

if __name__ == "__main__":
    # apple_finances = Financial_data.from_ticker_cik("AAPL", "0000320193", 11)
    # apple_finances.save_financials()
    apple_finances = Financial_data("AAPL", "0000320193", 1)
    with open(FINANCIALS_DIR / "company_facts", "w") as file:
        json.dump(apple_finances._get_facts(),file, indent=4)

    

