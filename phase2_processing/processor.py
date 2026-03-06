"""
Phase 2: Data Processing

- Clean scraped HTML/data
- Normalize numbers
- Convert to structured JSON
- Add metadata
- Chunk by logical sections
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .chunker import TextChunker


class DataProcessor:
    """Process and structure scraped data"""
    
    BASE_DIR = Path(__file__).parent.parent / "data"
    RAW_DIR = BASE_DIR / "raw"
    STRUCTURED_DIR = BASE_DIR / "structured"
    
    def __init__(self):
        self.STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
        self.chunker = TextChunker()
    
    def load_raw_data(self) -> Dict:
        """Load raw scraped data"""
        raw_file = self.RAW_DIR / "scraped_data.json"
        if not raw_file.exists():
            raise FileNotFoundError(f"Raw data not found at {raw_file}. Run scraper first.")
        
        with open(raw_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def process_funds(self, funds: List[Dict]) -> List[Dict]:
        """Process and clean fund data"""
        processed = []
        
        for fund in funds:
            processed_fund = self._process_single_fund(fund)
            processed.append(processed_fund)
        
        return processed
    
    def _process_single_fund(self, fund: Dict) -> Dict:
        """Process a single fund's data"""
        processed = {
            "id": self._generate_fund_id(fund),
            "fund_name": self._clean_text(fund.get("fund_name")),
            "amc_name": self._clean_text(fund.get("amc_name")),
            "category": self._normalize_category(fund.get("category")),
            "source_url": fund.get("source_url"),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            
            "expense_ratio": self._normalize_percentage(fund.get("expense_ratio")),
            "expense_ratio_numeric": self._to_float(fund.get("expense_ratio_numeric")),
            
            "exit_load": self._normalize_exit_load(fund.get("exit_load")),
            "lock_in_period": self._normalize_lock_in(fund.get("lock_in_period"), fund.get("source_url", "")),
            
            "riskometer": fund.get("riskometer"),
            "benchmark": self._clean_text(fund.get("benchmark")),
            
            "minimum_sip": self._normalize_currency(fund.get("minimum_sip")),
            "minimum_sip_numeric": self._to_float(fund.get("minimum_sip_numeric")),
            
            "aum": fund.get("aum"),
            "aum_numeric": self._to_float(fund.get("aum_numeric")),
            
            "fund_manager": self._clean_text(fund.get("fund_manager")),
            
            "returns": self._process_returns(fund.get("returns", {})),
            
            "nav": fund.get("nav"),
            "nav_date": fund.get("nav_date"),
        }
        
        processed["text_content"] = self._generate_text_content(processed)
        processed["chunks"] = self.chunker.chunk_fund_data(processed)
        
        return processed
    
    def _generate_fund_id(self, fund: Dict) -> str:
        """Generate unique ID for fund"""
        url = fund.get("source_url", "")
        if url:
            return url.split("/")[-1]
        name = fund.get("fund_name", "unknown")
        return re.sub(r'[^a-z0-9]', '-', name.lower())
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text"""
        if not text:
            return None
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text if text else None
    
    def _normalize_category(self, category: Optional[str]) -> Optional[str]:
        """Normalize fund category"""
        if not category:
            return None
        
        category_map = {
            'large cap': 'Large Cap',
            'largecap': 'Large Cap',
            'mid cap': 'Mid Cap',
            'midcap': 'Mid Cap',
            'small cap': 'Small Cap',
            'smallcap': 'Small Cap',
            'multi cap': 'Multi Cap',
            'multicap': 'Multi Cap',
            'flexi cap': 'Flexi Cap',
            'flexicap': 'Flexi Cap',
            'elss': 'ELSS (Tax Saver)',
            'tax saver': 'ELSS (Tax Saver)',
            'hybrid': 'Hybrid',
            'balanced': 'Balanced',
            'debt': 'Debt',
            'liquid': 'Liquid',
            'index': 'Index',
            'focused': 'Focused',
            'value': 'Value',
            'sectoral': 'Sectoral',
            'thematic': 'Thematic',
        }
        
        cat_lower = category.lower()
        for key, value in category_map.items():
            if key in cat_lower:
                return value
        
        return category
    
    def _normalize_percentage(self, value: Optional[str]) -> Optional[str]:
        """Normalize percentage values"""
        if not value:
            return None
        
        match = re.search(r'([0-9]+\.?[0-9]*)', str(value))
        if match:
            num = float(match.group(1))
            return f"{num:.2f}%"
        return value
    
    def _normalize_exit_load(self, value: Optional[str]) -> Optional[str]:
        """Normalize exit load information"""
        if not value:
            return "Not specified"
        
        value_lower = value.lower()
        if 'nil' in value_lower or 'no exit' in value_lower or value_lower == '0%':
            return "Nil"
        
        match = re.search(r'([0-9]+\.?[0-9]*)\s*%', value)
        if match:
            pct = float(match.group(1))
            duration_match = re.search(r'(\d+)\s*(year|month|day)', value, re.IGNORECASE)
            if duration_match:
                return f"{pct}% if redeemed within {duration_match.group(1)} {duration_match.group(2)}(s)"
            return f"{pct}%"
        
        return value
    
    def _normalize_lock_in(self, value: Optional[str], url: str = "") -> str:
        """Normalize lock-in period"""
        if 'elss' in url.lower() or 'tax-saver' in url.lower():
            return "3 Years (ELSS - Tax Saver Fund)"
        
        if not value:
            return "Nil"
        
        value_lower = value.lower()
        if 'nil' in value_lower or 'no lock' in value_lower or 'none' in value_lower:
            return "Nil"
        
        if 'elss' in value_lower or '3 year' in value_lower:
            return "3 Years (ELSS - Tax Saver Fund)"
        
        match = re.search(r'(\d+)\s*(year|month|day)', value, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2).capitalize()}(s)"
        
        return value
    
    def _normalize_currency(self, value: Optional[str]) -> Optional[str]:
        """Normalize currency values"""
        if not value:
            return None
        
        match = re.search(r'([0-9,]+)', str(value))
        if match:
            num = match.group(1).replace(',', '')
            try:
                num_val = int(num)
                return f"₹{num_val:,}"
            except ValueError:
                pass
        
        return value
    
    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _process_returns(self, returns: Dict) -> Dict:
        """Process returns data"""
        processed = {}
        
        for key, value in returns.items():
            if value:
                match = re.search(r'([+-]?[0-9]+\.?[0-9]*)', str(value))
                if match:
                    processed[key] = f"{float(match.group(1)):.2f}%"
                else:
                    processed[key] = value
        
        return processed
    
    def _generate_text_content(self, fund: Dict) -> str:
        """Generate searchable text content for the fund"""
        parts = []
        
        if fund.get("fund_name"):
            parts.append(f"Fund Name: {fund['fund_name']}")
        
        if fund.get("amc_name"):
            parts.append(f"AMC: {fund['amc_name']}")
        
        if fund.get("category"):
            parts.append(f"Category: {fund['category']}")
        
        if fund.get("expense_ratio"):
            parts.append(f"Expense Ratio: {fund['expense_ratio']}")
        
        if fund.get("exit_load"):
            parts.append(f"Exit Load: {fund['exit_load']}")
        
        if fund.get("lock_in_period"):
            parts.append(f"Lock-in Period: {fund['lock_in_period']}")
        
        if fund.get("riskometer"):
            parts.append(f"Risk Level: {fund['riskometer']}")
        
        if fund.get("benchmark"):
            parts.append(f"Benchmark: {fund['benchmark']}")
        
        if fund.get("minimum_sip"):
            parts.append(f"Minimum SIP: {fund['minimum_sip']}")
        
        if fund.get("aum"):
            parts.append(f"AUM: {fund['aum']}")
        
        if fund.get("fund_manager"):
            parts.append(f"Fund Manager: {fund['fund_manager']}")
        
        if fund.get("returns"):
            returns_text = []
            for period, value in fund["returns"].items():
                if value:
                    period_label = period.replace("_", " ").title()
                    returns_text.append(f"{period_label}: {value}")
            if returns_text:
                parts.append("Returns: " + ", ".join(returns_text))
        
        return "\n".join(parts)
    
    def process_help_pages(self, help_pages: List[Dict]) -> List[Dict]:
        """Process help page data"""
        processed = []
        
        for page in help_pages:
            processed_page = self._process_help_page(page)
            processed.append(processed_page)
        
        return processed
    
    def _process_help_page(self, page: Dict) -> Dict:
        """Process a single help page"""
        processed = {
            "id": f"help_{page.get('category', 'unknown')}",
            "category": page.get("category"),
            "description": page.get("description"),
            "source_url": page.get("source_url"),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "title": page.get("title"),
            "content": page.get("content", []),
            "faqs": page.get("faqs", []),
            "steps": page.get("steps", []),
        }
        
        if "capital_gains_info" in page:
            processed["capital_gains_info"] = page["capital_gains_info"]
        
        if "elss_info" in page:
            processed["elss_info"] = page["elss_info"]
        
        if "exit_load_info" in page:
            processed["exit_load_info"] = page["exit_load_info"]
        
        processed["text_content"] = self._generate_help_text_content(processed)
        processed["chunks"] = self.chunker.chunk_help_data(processed)
        
        return processed
    
    def _generate_help_text_content(self, page: Dict) -> str:
        """Generate searchable text content for help page"""
        parts = []
        
        if page.get("title"):
            parts.append(f"Topic: {page['title']}")
        
        if page.get("content"):
            parts.extend(page["content"])
        
        if page.get("steps"):
            parts.append("Steps:")
            parts.extend(page["steps"])
        
        if page.get("capital_gains_info"):
            info = page["capital_gains_info"]
            parts.append("\nCapital Gains Information:")
            if info.get("download_steps"):
                parts.append("How to download capital gains statement:")
                parts.extend(info["download_steps"])
            if info.get("stcg_info"):
                parts.append(info["stcg_info"])
            if info.get("ltcg_info"):
                parts.append(info["ltcg_info"])
        
        if page.get("elss_info"):
            info = page["elss_info"]
            parts.append("\nELSS Information:")
            parts.append(f"Lock-in Period: {info.get('lock_in_period', '3 Years')}")
            parts.append(f"Tax Benefit: {info.get('tax_benefit', 'Deduction under Section 80C')}")
            if info.get("description"):
                parts.append(info["description"])
        
        if page.get("exit_load_info"):
            info = page["exit_load_info"]
            parts.append("\nExit Load Information:")
            if info.get("description"):
                parts.append(info["description"])
            if info.get("common_rules"):
                parts.extend(info["common_rules"])
        
        return "\n".join(parts)
    
    def run(self) -> Dict:
        """Run complete processing pipeline"""
        print("=" * 60)
        print("PHASE 2: Data Processing")
        print("=" * 60)
        
        raw_data = self.load_raw_data()
        
        print(f"\nProcessing {len(raw_data.get('funds', []))} funds...")
        processed_funds = self.process_funds(raw_data.get("funds", []))
        
        print(f"Processing {len(raw_data.get('help_pages', []))} help pages...")
        processed_help = self.process_help_pages(raw_data.get("help_pages", []))
        
        result = {
            "funds": processed_funds,
            "help_pages": processed_help,
            "metadata": {
                "total_funds": len(processed_funds),
                "total_help_pages": len(processed_help),
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        output_path = self.STRUCTURED_DIR / "funds.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        all_chunks = []
        for fund in processed_funds:
            all_chunks.extend(fund.get("chunks", []))
        for help_page in processed_help:
            all_chunks.extend(help_page.get("chunks", []))
        
        chunks_path = self.STRUCTURED_DIR / "chunks.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Saved structured data to {output_path}")
        print(f"[OK] Saved {len(all_chunks)} chunks to {chunks_path}")
        print(f"  - Funds processed: {len(processed_funds)}")
        print(f"  - Help pages processed: {len(processed_help)}")
        
        return result


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()
