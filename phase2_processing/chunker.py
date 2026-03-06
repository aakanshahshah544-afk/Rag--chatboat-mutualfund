"""
Text Chunker for RAG

Chunks fund and help page data into smaller pieces
for better retrieval accuracy.
"""

from typing import Dict, List
import hashlib


class TextChunker:
    """Chunk text content for embedding"""
    
    MAX_CHUNK_SIZE = 500
    OVERLAP = 50
    
    def chunk_fund_data(self, fund: Dict) -> List[Dict]:
        """Create chunks from fund data"""
        chunks = []
        fund_name = fund.get("fund_name", "Unknown Fund")
        source_url = fund.get("source_url", "")
        
        basic_info = self._create_basic_info_chunk(fund)
        if basic_info:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "basic"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "basic_info",
                "content": basic_info,
                "source_url": source_url,
            })
        
        expense_chunk = self._create_expense_chunk(fund)
        if expense_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "expense"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "expense_ratio",
                "content": expense_chunk,
                "source_url": source_url,
            })
        
        exit_load_chunk = self._create_exit_load_chunk(fund)
        if exit_load_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "exit_load"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "exit_load",
                "content": exit_load_chunk,
                "source_url": source_url,
            })
        
        lock_in_chunk = self._create_lock_in_chunk(fund)
        if lock_in_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "lock_in"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "lock_in_period",
                "content": lock_in_chunk,
                "source_url": source_url,
            })
        
        sip_chunk = self._create_sip_chunk(fund)
        if sip_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "sip"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "minimum_sip",
                "content": sip_chunk,
                "source_url": source_url,
            })
        
        benchmark_chunk = self._create_benchmark_chunk(fund)
        if benchmark_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "benchmark"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "benchmark",
                "content": benchmark_chunk,
                "source_url": source_url,
            })
        
        returns_chunk = self._create_returns_chunk(fund)
        if returns_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "returns"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "returns",
                "content": returns_chunk,
                "source_url": source_url,
            })
        
        full_chunk = fund.get("text_content", "")
        if full_chunk:
            chunks.append({
                "id": self._generate_chunk_id(fund.get("id", ""), "full"),
                "fund_id": fund.get("id"),
                "fund_name": fund_name,
                "chunk_type": "full_info",
                "content": full_chunk,
                "source_url": source_url,
            })
        
        return chunks
    
    def _create_basic_info_chunk(self, fund: Dict) -> str:
        """Create basic fund information chunk"""
        parts = []
        
        if fund.get("fund_name"):
            parts.append(f"{fund['fund_name']} is a mutual fund")
        
        if fund.get("amc_name"):
            parts.append(f"managed by {fund['amc_name']}")
        
        if fund.get("category"):
            parts.append(f"It is a {fund['category']} fund.")
        
        if fund.get("riskometer"):
            parts.append(f"Risk level: {fund['riskometer']}.")
        
        if fund.get("aum"):
            parts.append(f"Assets Under Management (AUM): {fund['aum']}.")
        
        if fund.get("fund_manager"):
            parts.append(f"Fund Manager: {fund['fund_manager']}.")
        
        return " ".join(parts) if parts else ""
    
    def _create_expense_chunk(self, fund: Dict) -> str:
        """Create expense ratio chunk"""
        if not fund.get("expense_ratio"):
            return ""
        
        parts = [
            f"The expense ratio of {fund.get('fund_name', 'this fund')} is {fund['expense_ratio']}.",
            "Expense ratio is the annual fee charged by the fund for management.",
        ]
        
        return " ".join(parts)
    
    def _create_exit_load_chunk(self, fund: Dict) -> str:
        """Create exit load chunk"""
        if not fund.get("exit_load"):
            return ""
        
        parts = [
            f"The exit load for {fund.get('fund_name', 'this fund')} is {fund['exit_load']}.",
            "Exit load is the fee charged when you redeem your units before a specified period.",
        ]
        
        return " ".join(parts)
    
    def _create_lock_in_chunk(self, fund: Dict) -> str:
        """Create lock-in period chunk"""
        lock_in = fund.get("lock_in_period", "Nil")
        
        parts = [f"The lock-in period for {fund.get('fund_name', 'this fund')} is {lock_in}."]
        
        if "ELSS" in lock_in or "3 Year" in lock_in:
            parts.append("ELSS (Equity Linked Savings Scheme) funds have a mandatory 3-year lock-in period.")
            parts.append("They offer tax benefits under Section 80C up to ₹1,50,000 per year.")
        elif lock_in == "Nil":
            parts.append("This means you can redeem your investment anytime without restrictions.")
        
        return " ".join(parts)
    
    def _create_sip_chunk(self, fund: Dict) -> str:
        """Create minimum SIP chunk"""
        if not fund.get("minimum_sip"):
            return ""
        
        parts = [
            f"The minimum SIP amount for {fund.get('fund_name', 'this fund')} is {fund['minimum_sip']}.",
            "SIP (Systematic Investment Plan) allows you to invest a fixed amount regularly.",
        ]
        
        return " ".join(parts)
    
    def _create_benchmark_chunk(self, fund: Dict) -> str:
        """Create benchmark chunk"""
        if not fund.get("benchmark"):
            return ""
        
        parts = [
            f"The benchmark index for {fund.get('fund_name', 'this fund')} is {fund['benchmark']}.",
            "A benchmark is a standard against which the fund's performance is measured.",
        ]
        
        return " ".join(parts)
    
    def _create_returns_chunk(self, fund: Dict) -> str:
        """Create returns chunk"""
        returns = fund.get("returns", {})
        if not returns:
            return ""
        
        parts = [f"Returns for {fund.get('fund_name', 'this fund')}:"]
        
        if returns.get("1_year"):
            parts.append(f"1 Year Return: {returns['1_year']}.")
        if returns.get("3_year"):
            parts.append(f"3 Year Return: {returns['3_year']}.")
        if returns.get("5_year"):
            parts.append(f"5 Year Return: {returns['5_year']}.")
        if returns.get("since_inception"):
            parts.append(f"Since Inception: {returns['since_inception']}.")
        
        return " ".join(parts) if len(parts) > 1 else ""
    
    def chunk_help_data(self, page: Dict) -> List[Dict]:
        """Create chunks from help page data"""
        chunks = []
        source_url = page.get("source_url", "")
        category = page.get("category", "general")
        
        main_content = page.get("text_content", "")
        if main_content:
            text_chunks = self._split_text(main_content)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "id": self._generate_chunk_id(page.get("id", ""), f"content_{i}"),
                    "page_id": page.get("id"),
                    "category": category,
                    "chunk_type": "help_content",
                    "content": chunk_text,
                    "source_url": source_url,
                })
        
        if page.get("capital_gains_info"):
            info = page["capital_gains_info"]
            
            if info.get("download_steps"):
                steps_text = "How to download capital gains statement from Groww:\n"
                steps_text += "\n".join(info["download_steps"])
                chunks.append({
                    "id": self._generate_chunk_id(page.get("id", ""), "cg_download"),
                    "page_id": page.get("id"),
                    "category": "capital_gains",
                    "chunk_type": "capital_gains_download",
                    "content": steps_text,
                    "source_url": source_url,
                })
            
            tax_parts = []
            if info.get("stcg_info"):
                tax_parts.append(info["stcg_info"])
            if info.get("ltcg_info"):
                tax_parts.append(info["ltcg_info"])
            if info.get("tax_rates"):
                for rate_type, rate in info["tax_rates"].items():
                    tax_parts.append(f"{rate_type.replace('_', ' ').title()}: {rate}")
            
            if tax_parts:
                chunks.append({
                    "id": self._generate_chunk_id(page.get("id", ""), "cg_tax"),
                    "page_id": page.get("id"),
                    "category": "capital_gains",
                    "chunk_type": "tax_info",
                    "content": "Capital Gains Tax Information:\n" + "\n".join(tax_parts),
                    "source_url": source_url,
                })
        
        if page.get("elss_info"):
            info = page["elss_info"]
            elss_text = "ELSS (Equity Linked Savings Scheme) Information:\n"
            elss_text += f"Lock-in Period: {info.get('lock_in_period', '3 Years')}\n"
            elss_text += f"Tax Benefit: {info.get('tax_benefit', 'Deduction under Section 80C')}\n"
            if info.get("description"):
                elss_text += info["description"]
            
            chunks.append({
                "id": self._generate_chunk_id(page.get("id", ""), "elss"),
                "page_id": page.get("id"),
                "category": "elss",
                "chunk_type": "elss_info",
                "content": elss_text,
                "source_url": source_url,
            })
        
        if page.get("exit_load_info"):
            info = page["exit_load_info"]
            exit_text = "Exit Load Information:\n"
            if info.get("description"):
                exit_text += info["description"] + "\n"
            if info.get("common_rules"):
                exit_text += "\nCommon Exit Load Rules:\n"
                exit_text += "\n".join(f"- {rule}" for rule in info["common_rules"])
            
            chunks.append({
                "id": self._generate_chunk_id(page.get("id", ""), "exit_load"),
                "page_id": page.get("id"),
                "category": "exit_load",
                "chunk_type": "exit_load_info",
                "content": exit_text,
                "source_url": source_url,
            })
        
        if page.get("steps"):
            steps_text = f"{page.get('title', 'Steps')}:\n"
            steps_text += "\n".join(page["steps"])
            chunks.append({
                "id": self._generate_chunk_id(page.get("id", ""), "steps"),
                "page_id": page.get("id"),
                "category": category,
                "chunk_type": "steps",
                "content": steps_text,
                "source_url": source_url,
            })
        
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if len(text) <= self.MAX_CHUNK_SIZE:
            return [text]
        
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.MAX_CHUNK_SIZE:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:self.MAX_CHUNK_SIZE]]
    
    def _generate_chunk_id(self, base_id: str, suffix: str) -> str:
        """Generate unique chunk ID"""
        raw = f"{base_id}_{suffix}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
