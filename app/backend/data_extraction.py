import time
import requests
from copy import deepcopy
from schema import SCHEMA
from tag_map import TAG_MAP

HEADERS_SEC = {
    "User-Agent": "Louis Etien louis-etien@hotmail.fr"
}

def get_filing_url(cik):
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
        return None
    
    cik_no_zero = str(int(cik))

    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession}/{document}"

def get_company_facts(cik: str):

    cik = cik.zfill(10)

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    response = requests.get(url, headers=HEADERS_SEC)

    response.raise_for_status()

    return response.json()

def get_latest_fact(facts, tag):

    try:

        entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]

        annual_entries = [
            e for e in entries
            if e.get("fp") == "FY"
        ]

        if not annual_entries:
            return None

        latest = sorted(
            annual_entries,
            key=lambda x: x["end"]
        )[-1]

        return latest["val"]

    except KeyError:

        return None
    
def extract_financials(cik):

    facts = get_company_facts(cik)

    result = deepcopy(SCHEMA)

    for section in TAG_MAP:

        for metric in TAG_MAP[section]:

            tags = TAG_MAP[section][metric]

            for tag in tags:

                value = get_latest_fact(facts, tag)

                if value is not None:
                    result[section][metric] = value
                    break

    # compute derived metrics
    if result["cashflow_statement"]["operating_cash_flow"] and \
       result["cashflow_statement"]["capex"]:

        ocf = result["cashflow_statement"]["operating_cash_flow"]
        capex = result["cashflow_statement"]["capex"]

        result["cashflow_statement"]["free_cash_flow"] = ocf - abs(capex)

    return result

if __name__ == "__main__":
    print(extract_financials("0000320193")) 