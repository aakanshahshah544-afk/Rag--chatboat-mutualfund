"""
Phase 1: Groww Mutual Fund Page Scraper

Scrapes mutual fund data from Groww including:
- Fund Name, AMC, Category, Expense Ratio, Exit Load
- Lock-in Period, Riskometer, Benchmark, Min SIP, AUM
- Fund Manager, Returns table, Source URL
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .fund_urls import get_all_fund_urls, FUND_URLS
from .help_scraper import HelpPageScraper


class GrowwScraper:
    """Scraper for Groww mutual fund pages"""
    
    BASE_DIR = Path(__file__).parent.parent / "data"
    RAW_DIR = BASE_DIR / "raw"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create necessary directories"""
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        (self.BASE_DIR / "structured").mkdir(parents=True, exist_ok=True)
        (self.BASE_DIR / "embeddings").mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch HTML content from URL with retries"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def parse_fund_page(self, html: str, url: str, amc: str) -> Dict:
        """Extract fund data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "source_url": url,
            "amc_name": amc,
            "last_scraped": datetime.utcnow().isoformat() + "Z",
            "fund_name": None,
            "category": None,
            "expense_ratio": None,
            "expense_ratio_numeric": None,
            "exit_load": None,
            "lock_in_period": None,
            "riskometer": None,
            "benchmark": None,
            "minimum_sip": None,
            "minimum_sip_numeric": None,
            "aum": None,
            "aum_numeric": None,
            "fund_manager": None,
            "returns": {},
            "nav": None,
            "nav_date": None,
        }
        
        data["fund_name"] = self._extract_fund_name(soup)
        data["category"] = self._extract_category(soup)
        expense_ratio = self._extract_expense_ratio(soup)
        data["expense_ratio"] = expense_ratio
        data["expense_ratio_numeric"] = self._parse_percentage(expense_ratio)
        data["exit_load"] = self._extract_exit_load(soup)
        data["lock_in_period"] = self._extract_lock_in_period(soup, url)
        data["riskometer"] = self._extract_riskometer(soup)
        data["benchmark"] = self._extract_benchmark(soup)
        min_sip = self._extract_min_sip(soup)
        data["minimum_sip"] = min_sip
        data["minimum_sip_numeric"] = self._parse_currency(min_sip)
        aum = self._extract_aum(soup)
        data["aum"] = aum
        data["aum_numeric"] = self._parse_aum(aum)
        data["fund_manager"] = self._extract_fund_manager(soup)
        data["returns"] = self._extract_returns(soup)
        nav_data = self._extract_nav(soup)
        data["nav"] = nav_data.get("nav")
        data["nav_date"] = nav_data.get("date")
        
        return data
    
    def _extract_fund_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund name from page"""
        selectors = [
            'h1.mfnH1',
            'h1[class*="mfName"]',
            'h1[class*="fundName"]',
            '.mfnHead h1',
            'h1'
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 5:
                    return name
        
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            if 'Fund' in title_text:
                name = title_text.split('|')[0].strip()
                name = name.replace(' - Groww', '').strip()
                return name
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund category"""
        category_patterns = [
            r'(Large Cap|Mid Cap|Small Cap|Multi Cap|Flexi Cap|ELSS|Equity Hybrid|Balanced|Debt|Liquid|Index|Sectoral|Thematic|Value|Focused)',
        ]
        
        selectors = [
            '[class*="category"]',
            '[class*="subCat"]',
            '.mfnSub',
            'span[class*="type"]',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                for pattern in category_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1)
                if text and len(text) < 50:
                    return text
        
        page_text = soup.get_text(separator=' ')
        for pattern in category_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio"""
        page_text = soup.get_text(separator=' | ').lower()
        match = re.search(r'expense\s*ratio[\s:|]*([0-9]+\.?[0-9]*)\s*%', page_text)
        if match:
            return f"{match.group(1)}%"
        return None
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract exit load information"""
        page_text = soup.get_text(separator=' | ')
        
        # Priority to exact Nil match
        match = re.search(r'exit\s*load[\s:|]*(0\s*%|nil|none)', page_text, re.IGNORECASE)
        if match:
            text_val = match.group(1).strip()
            return "Nil" if text_val.lower() in ['nil', 'none'] else text_val
            
        match = re.search(r'exit\s*load[\s:|]*([^\n|]{5,100})', page_text, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if 'stamp duty' not in extracted.lower() and 'fee payable' not in extracted.lower() and 'a fee' not in extracted.lower():
                return extracted
        
        return None
    
    def _extract_lock_in_period(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract lock-in period (especially for ELSS funds)"""
        if 'elss' in url.lower() or 'tax-saver' in url.lower():
            return "3 Years (ELSS)"
        
        for elem in soup.find_all(['div', 'span', 'td', 'p']):
            text = elem.get_text(strip=True).lower()
            if 'lock' in text and ('in' in text or 'period' in text):
                full_text = elem.get_text(strip=True)
                if 'nil' in full_text.lower() or 'no lock' in full_text.lower():
                    return "Nil"
                match = re.search(r'(\d+)\s*(year|month|day)', full_text, re.IGNORECASE)
                if match:
                    return f"{match.group(1)} {match.group(2).capitalize()}s"
        
        page_text = soup.get_text(separator=' ').lower()
        if 'elss' in page_text or 'tax saver' in page_text or 'tax saving' in page_text:
            if 'lock' in page_text:
                return "3 Years (ELSS)"
        
        return "Nil"
    
    def _extract_riskometer(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract riskometer level"""
        risk_levels = ['Low', 'Low to Moderate', 'Moderate', 'Moderately High', 'High', 'Very High']
        
        for elem in soup.find_all(['div', 'span', 'td', 'p']):
            text = elem.get_text(strip=True)
            for level in risk_levels:
                if level.lower() in text.lower():
                    if 'risk' in text.lower() or 'riskometer' in text.lower():
                        return level
        
        page_text = soup.get_text(separator=' ')
        for level in risk_levels:
            pattern = rf'risk[ometer]*[\s:|]*{re.escape(level)}'
            if re.search(pattern, page_text, re.IGNORECASE):
                return level
            pattern = rf'{re.escape(level)}[\s:|]*risk'
            if re.search(pattern, page_text, re.IGNORECASE):
                return level
        
        return None
    
    def _extract_benchmark(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract benchmark index"""
        for elem in soup.find_all(['div', 'span', 'td', 'p']):
            text = elem.get_text(strip=True).lower()
            if 'benchmark' in text:
                full_text = elem.get_text(strip=True)
                next_elem = elem.find_next_sibling()
                if next_elem:
                    benchmark_text = next_elem.get_text(strip=True)
                    if benchmark_text and len(benchmark_text) < 100:
                        return benchmark_text
                
                if ':' in full_text:
                    return full_text.split(':', 1)[1].strip()
        
        benchmark_patterns = [
            r'(NIFTY\s*(?:50|100|500|Next 50|Midcap|Smallcap)[^\n]*)',
            r'(BSE\s*(?:SENSEX|100|200|500|Midcap|Smallcap)[^\n]*)',
            r'(S&P\s*BSE[^\n]*)',
        ]
        
        page_text = soup.get_text(separator=' ')
        for pattern in benchmark_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_min_sip(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract minimum SIP amount"""
        page_text = soup.get_text(separator=' | ')
        match = re.search(r'min(?:imum)?[\w.\s]*sip[\s:|]*₹?\s*([0-9,]+)', page_text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
        return "₹500"
    
    def _extract_aum(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Assets Under Management"""
        page_text = soup.get_text(separator=' | ')
        match = re.search(r'(?:aum|asset|fund size)[\s:|]*₹?\s*([0-9,]+\.?[0-9]*)\s*(Cr|Crore|L|Lakh)', page_text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)} {match.group(2)}"
        return None
    
    def _extract_fund_manager(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund manager name"""
        for elem in soup.find_all(['div', 'span', 'td', 'p']):
            text = elem.get_text(strip=True).lower()
            if 'fund manager' in text or 'managed by' in text:
                full_text = elem.get_text(strip=True)
                next_elem = elem.find_next_sibling()
                if next_elem:
                    manager = next_elem.get_text(strip=True)
                    if manager and len(manager) < 100:
                        return manager
                
                if ':' in full_text:
                    return full_text.split(':', 1)[1].strip()
        
        return None
    
    def _extract_returns(self, soup: BeautifulSoup) -> Dict:
        """Extract returns data"""
        returns = {
            "1_year": None,
            "3_year": None,
            "5_year": None,
            "since_inception": None
        }
        
        for elem in soup.find_all(['div', 'span', 'td']):
            text = elem.get_text(strip=True).lower()
            
            if '1' in text and ('year' in text or 'yr' in text):
                match = re.search(r'([+-]?\d+\.?\d*)\s*%', elem.get_text())
                if match:
                    returns["1_year"] = f"{match.group(1)}%"
            
            if '3' in text and ('year' in text or 'yr' in text):
                match = re.search(r'([+-]?\d+\.?\d*)\s*%', elem.get_text())
                if match:
                    returns["3_year"] = f"{match.group(1)}%"
            
            if '5' in text and ('year' in text or 'yr' in text):
                match = re.search(r'([+-]?\d+\.?\d*)\s*%', elem.get_text())
                if match:
                    returns["5_year"] = f"{match.group(1)}%"
        
        return returns
    
    def _extract_nav(self, soup: BeautifulSoup) -> Dict:
        """Extract current NAV"""
        nav_data = {"nav": None, "date": None}
        
        for elem in soup.find_all(['div', 'span']):
            text = elem.get_text(strip=True).lower()
            if 'nav' in text:
                full_text = elem.get_text(strip=True)
                match = re.search(r'₹?\s*([0-9,]+\.?[0-9]*)', full_text)
                if match:
                    nav_data["nav"] = f"₹{match.group(1)}"
                    break
        
        return nav_data
    
    def _parse_percentage(self, value: Optional[str]) -> Optional[float]:
        """Parse percentage string to float"""
        if not value:
            return None
        match = re.search(r'([0-9]+\.?[0-9]*)', value)
        if match:
            return float(match.group(1))
        return None
    
    def _parse_currency(self, value: Optional[str]) -> Optional[float]:
        """Parse currency string to float"""
        if not value:
            return None
        cleaned = re.sub(r'[₹,\s]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def _parse_aum(self, value: Optional[str]) -> Optional[float]:
        """Parse AUM to float (in crores)"""
        if not value:
            return None
        match = re.search(r'([0-9,]+\.?[0-9]*)\s*(Cr|Crore|L|Lakh)', value, re.IGNORECASE)
        if match:
            num = float(match.group(1).replace(',', ''))
            unit = match.group(2).lower()
            if unit in ['l', 'lakh']:
                return num / 100
            return num
        return None
    
    def save_raw_html(self, html: str, url: str):
        """Save raw HTML to file"""
        filename = url.split('/')[-1] + '.html'
        filepath = self.RAW_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def scrape_all_funds(self) -> List[Dict]:
        """Scrape all configured fund URLs"""
        all_data = []
        fund_urls = get_all_fund_urls()
        
        print(f"Scraping {len(fund_urls)} mutual fund pages...")
        
        for fund_info in tqdm(fund_urls, desc="Scraping funds"):
            url = fund_info["url"]
            amc = fund_info["amc"]
            
            html = self.fetch_page(url)
            if html:
                self.save_raw_html(html, url)
                fund_data = self.parse_fund_page(html, url, amc)
                all_data.append(fund_data)
                print(f"  [OK] Scraped: {fund_data.get('fund_name', url)}")
            else:
                print(f"  [FAIL] Failed: {url}")
            
            time.sleep(1)
        
        return all_data
    
    def scrape_help_pages(self) -> List[Dict]:
        """Scrape help pages"""
        help_scraper = HelpPageScraper()
        return help_scraper.scrape_all_help_pages()
    
    def run(self) -> Dict:
        """Run complete scraping pipeline"""
        print("=" * 60)
        print("PHASE 1: Web Scraping")
        print("=" * 60)
        
        funds_data = self.scrape_all_funds()
        help_data = self.scrape_help_pages()
        
        result = {
            "funds": funds_data,
            "help_pages": help_data,
            "metadata": {
                "total_funds": len(funds_data),
                "total_help_pages": len(help_data),
                "scraped_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        raw_output_path = self.RAW_DIR / "scraped_data.json"
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Saved raw data to {raw_output_path}")
        print(f"  - Funds scraped: {len(funds_data)}")
        print(f"  - Help pages scraped: {len(help_data)}")
        
        return result


if __name__ == "__main__":
    scraper = GrowwScraper()
    scraper.run()
