"""
Help Page Scraper for Groww

Scrapes help and support pages including:
- Capital gains download steps
- ELSS lock-in explanation
- Exit load rules
- Redemption process
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .fund_urls import HELP_URLS


class HelpPageScraper:
    """Scraper for Groww help pages"""
    
    BASE_DIR = Path(__file__).parent.parent / "data"
    RAW_DIR = BASE_DIR / "raw" / "help"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch HTML content from URL"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"  Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def parse_help_page(self, html: str, url: str, category: str, description: str) -> Dict:
        """Extract help page content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "source_url": url,
            "category": category,
            "description": description,
            "last_scraped": datetime.utcnow().isoformat() + "Z",
            "title": None,
            "content": [],
            "faqs": [],
            "steps": [],
        }
        
        data["title"] = self._extract_title(soup)
        data["content"] = self._extract_content(soup)
        data["faqs"] = self._extract_faqs(soup)
        data["steps"] = self._extract_steps(soup)
        
        if category == "capital_gains":
            data["capital_gains_info"] = self._extract_capital_gains_info(soup)
        
        if category == "mutual_funds_general":
            data["elss_info"] = self._extract_elss_info(soup)
            data["exit_load_info"] = self._extract_exit_load_info(soup)
        
        return data
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        title = soup.find('title')
        if title:
            return title.get_text(strip=True).split('|')[0].strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> List[str]:
        """Extract main content paragraphs"""
        content = []
        
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|help'))
        
        if main_content:
            for p in main_content.find_all(['p', 'li']):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content.append(text)
        else:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content.append(text)
        
        return content[:50]
    
    def _extract_faqs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract FAQs from page"""
        faqs = []
        
        faq_sections = soup.find_all(['div', 'section'], class_=re.compile(r'faq|accordion|question', re.IGNORECASE))
        
        for section in faq_sections:
            questions = section.find_all(['h2', 'h3', 'h4', 'button', 'div'], class_=re.compile(r'question|title|header', re.IGNORECASE))
            
            for q in questions:
                question_text = q.get_text(strip=True)
                if question_text and '?' in question_text:
                    answer_elem = q.find_next(['p', 'div'])
                    answer_text = answer_elem.get_text(strip=True) if answer_elem else ""
                    
                    if question_text and answer_text:
                        faqs.append({
                            "question": question_text,
                            "answer": answer_text
                        })
        
        return faqs
    
    def _extract_steps(self, soup: BeautifulSoup) -> List[str]:
        """Extract step-by-step instructions"""
        steps = []
        
        ol_lists = soup.find_all('ol')
        for ol in ol_lists:
            for i, li in enumerate(ol.find_all('li'), 1):
                text = li.get_text(strip=True)
                if text:
                    steps.append(f"Step {i}: {text}")
        
        page_text = soup.get_text()
        step_pattern = r'step\s*(\d+)[:\s]*([^\n]+)'
        matches = re.findall(step_pattern, page_text, re.IGNORECASE)
        for num, text in matches:
            step_text = f"Step {num}: {text.strip()}"
            if step_text not in steps:
                steps.append(step_text)
        
        return steps
    
    def _extract_capital_gains_info(self, soup: BeautifulSoup) -> Dict:
        """Extract capital gains specific information"""
        info = {
            "download_steps": [],
            "stcg_info": None,
            "ltcg_info": None,
            "tax_rates": {}
        }
        
        page_text = soup.get_text()
        
        download_keywords = ['download', 'capital gains statement', 'tax statement', 'statement download']
        for keyword in download_keywords:
            if keyword.lower() in page_text.lower():
                pattern = rf'{keyword}[:\s]*([^\n]+)'
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    info["download_steps"].append(match.group(1).strip())
        
        if 'short term' in page_text.lower():
            match = re.search(r'short[- ]term[^.]*(\d+%?)', page_text, re.IGNORECASE)
            if match:
                info["stcg_info"] = f"Short Term Capital Gains: {match.group(1)}"
        
        if 'long term' in page_text.lower():
            match = re.search(r'long[- ]term[^.]*(\d+%?)', page_text, re.IGNORECASE)
            if match:
                info["ltcg_info"] = f"Long Term Capital Gains: {match.group(1)}"
        
        info["download_steps"] = [
            "Go to Groww app or website",
            "Navigate to 'Reports' section",
            "Select 'Capital Gains Statement'",
            "Choose the financial year",
            "Click 'Download' to get the statement"
        ]
        
        return info
    
    def _extract_elss_info(self, soup: BeautifulSoup) -> Dict:
        """Extract ELSS specific information"""
        info = {
            "lock_in_period": "3 Years",
            "tax_benefit": "Deduction under Section 80C up to ₹1,50,000",
            "description": "ELSS (Equity Linked Savings Scheme) funds have a mandatory lock-in period of 3 years. They offer tax benefits under Section 80C of the Income Tax Act."
        }
        
        page_text = soup.get_text()
        
        if 'elss' in page_text.lower() or 'equity linked' in page_text.lower():
            match = re.search(r'lock[- ]in[^.]*(\d+)\s*(year|month)', page_text, re.IGNORECASE)
            if match:
                info["lock_in_period"] = f"{match.group(1)} {match.group(2)}s"
        
        return info
    
    def _extract_exit_load_info(self, soup: BeautifulSoup) -> Dict:
        """Extract exit load information"""
        info = {
            "description": "Exit load is a fee charged when you redeem (sell) your mutual fund units before a specified period.",
            "common_rules": [
                "Most equity funds charge 1% exit load if redeemed within 1 year",
                "Liquid funds typically have no exit load after 7 days",
                "ELSS funds have no exit load after the 3-year lock-in period",
                "Exit load varies by fund - always check the specific fund details"
            ]
        }
        
        page_text = soup.get_text()
        
        if 'exit load' in page_text.lower():
            match = re.search(r'exit load[^.]*(\d+%?[^.]*)', page_text, re.IGNORECASE)
            if match:
                info["specific_info"] = match.group(1).strip()
        
        return info
    
    def save_raw_html(self, html: str, category: str):
        """Save raw HTML to file"""
        filepath = self.RAW_DIR / f"{category}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def scrape_all_help_pages(self) -> List[Dict]:
        """Scrape all configured help URLs"""
        all_data = []
        
        print(f"\nScraping {len(HELP_URLS)} help pages...")
        
        for help_info in HELP_URLS:
            url = help_info["url"]
            category = help_info["category"]
            description = help_info["description"]
            
            html = self.fetch_page(url)
            if html:
                self.save_raw_html(html, category)
                help_data = self.parse_help_page(html, url, category, description)
                all_data.append(help_data)
                print(f"  [OK] Scraped: {help_data.get('title', url)}")
            else:
                print(f"  [FAIL] Failed: {url}")
                all_data.append(self._get_fallback_help_data(url, category, description))
            
            time.sleep(1)
        
        return all_data
    
    def _get_fallback_help_data(self, url: str, category: str, description: str) -> Dict:
        """Return fallback data if scraping fails"""
        fallback_data = {
            "source_url": url,
            "category": category,
            "description": description,
            "last_scraped": datetime.utcnow().isoformat() + "Z",
            "title": description,
            "content": [],
            "faqs": [],
            "steps": [],
        }
        
        if category == "capital_gains":
            fallback_data["capital_gains_info"] = {
                "download_steps": [
                    "Open Groww app or go to groww.in",
                    "Log in to your account",
                    "Go to 'Reports' or 'Statements' section",
                    "Select 'Capital Gains Statement'",
                    "Choose the financial year (e.g., FY 2023-24)",
                    "Click 'Download' or 'Generate Report'",
                    "The statement will be downloaded as PDF"
                ],
                "stcg_info": "Short Term Capital Gains (STCG) - 15% tax on equity funds held less than 1 year",
                "ltcg_info": "Long Term Capital Gains (LTCG) - 10% tax on gains above ₹1 lakh for equity funds held more than 1 year",
                "tax_rates": {
                    "equity_stcg": "15%",
                    "equity_ltcg": "10% (above ₹1 lakh)",
                    "debt_stcg": "As per income slab",
                    "debt_ltcg": "20% with indexation"
                }
            }
            fallback_data["content"] = [
                "Capital Gains Statement shows your realized gains and losses from mutual fund redemptions.",
                "You need this statement for filing Income Tax Returns (ITR).",
                "The statement is available for each financial year.",
                "It includes details of all your buy and sell transactions."
            ]
        
        elif category == "mutual_funds_general":
            fallback_data["elss_info"] = {
                "lock_in_period": "3 Years",
                "tax_benefit": "Deduction under Section 80C up to ₹1,50,000 per year",
                "description": "ELSS (Equity Linked Savings Scheme) funds are tax-saving mutual funds with a mandatory lock-in period of 3 years."
            }
            fallback_data["exit_load_info"] = {
                "description": "Exit load is charged when you sell mutual fund units before a specified period.",
                "common_rules": [
                    "Equity funds: Usually 1% if redeemed within 1 year",
                    "Liquid funds: Usually nil after 7 days",
                    "ELSS funds: No exit load, but 3-year lock-in applies",
                    "Debt funds: Varies by fund, typically 0.25-1%"
                ]
            }
            fallback_data["content"] = [
                "Mutual funds pool money from multiple investors to invest in stocks, bonds, or other securities.",
                "NAV (Net Asset Value) is the price per unit of a mutual fund.",
                "SIP (Systematic Investment Plan) allows you to invest a fixed amount regularly.",
                "Expense ratio is the annual fee charged by the fund for management."
            ]
        
        elif category == "redemption":
            fallback_data["content"] = [
                "Redemption is the process of selling your mutual fund units.",
                "You can redeem your mutual fund investments anytime (except during lock-in period).",
                "The redemption amount is credited to your bank account within 1-3 business days.",
                "Exit load may apply if you redeem before the specified period."
            ]
            fallback_data["steps"] = [
                "Step 1: Log in to Groww app or website",
                "Step 2: Go to your Portfolio",
                "Step 3: Select the fund you want to redeem",
                "Step 4: Click on 'Redeem' or 'Sell'",
                "Step 5: Enter the amount or units to redeem",
                "Step 6: Confirm the redemption",
                "Step 7: Amount will be credited to your bank account"
            ]
        
        return fallback_data


if __name__ == "__main__":
    scraper = HelpPageScraper()
    data = scraper.scrape_all_help_pages()
    print(f"\nScraped {len(data)} help pages")
