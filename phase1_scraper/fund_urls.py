"""URLs for Groww mutual fund pages to scrape"""

FUND_URLS = {
    "SBI Mutual Fund": [
        "https://groww.in/mutual-funds/sbi-bluechip-fund-direct-growth",
        "https://groww.in/mutual-funds/sbi-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/sbi-magnum-midcap-fund-direct-growth",
        "https://groww.in/mutual-funds/sbi-equity-hybrid-fund-direct-growth",
        "https://groww.in/mutual-funds/sbi-focused-equity-fund-direct-growth",
    ],
    "HDFC Mutual Fund": [
        "https://groww.in/mutual-funds/hdfc-top-100-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    ],
    "Axis Mutual Fund": [
        "https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/axis-bluechip-fund-direct-growth",
        "https://groww.in/mutual-funds/axis-midcap-fund-direct-growth",
        "https://groww.in/mutual-funds/axis-flexi-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/axis-elss-tax-saver-fund-direct-growth",
    ],
    "ICICI Prudential Mutual Fund": [
        "https://groww.in/mutual-funds/icici-prudential-bluechip-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-value-discovery-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-midcap-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-technology-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-equity-and-debt-fund-direct-growth",
    ],
    "Kotak Mutual Fund": [
        "https://groww.in/mutual-funds/kotak-flexicap-fund-direct-growth",
        "https://groww.in/mutual-funds/kotak-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/kotak-emerging-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/kotak-equity-opportunities-fund-direct-growth",
        "https://groww.in/mutual-funds/kotak-tax-saver-fund-direct-growth",
    ],
    "Groww Mutual Fund": [
        "https://groww.in/mutual-funds/groww-nifty-500-momentum-50-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/groww-aggressive-hybrid-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-india-railways-psu-index-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-arbitrage-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-multicap-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-overnight-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-india-defence-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/groww-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-liquid-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-smallcap-250-index-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-total-market-index-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-banking-financial-services-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-dynamic-bond-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-200-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-ev-new-age-automotive-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/groww-money-market-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-elss-tax-saver-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-non-cyclical-consumer-index-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-gold-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/groww-short-duration-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-value-fund-direct-growth",
        "https://groww.in/mutual-funds/groww-nifty-next-50-index-fund-direct-growth"
    ],
}

HELP_URLS = [
    {
        "url": "https://groww.in/help/mutual-funds",
        "category": "mutual_funds_general",
        "description": "General mutual fund help"
    },
    {
        "url": "https://groww.in/help/mutual-funds/redeem",
        "category": "redemption",
        "description": "How to redeem mutual funds"
    },
    {
        "url": "https://groww.in/help/tax/capital-gains",
        "category": "capital_gains",
        "description": "Capital gains and tax information"
    },
]

def get_all_fund_urls():
    """Return flat list of all fund URLs"""
    urls = []
    for amc, fund_list in FUND_URLS.items():
        for url in fund_list:
            urls.append({
                "url": url,
                "amc": amc
            })
    return urls
