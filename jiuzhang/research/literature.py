"""Enhanced literature search module for JiuZhang.

Searches arXiv, CrossRef, and other open access repositories.
Downloads and parses paper metadata and abstracts.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from typing import Optional
from datetime import datetime


# Mathematical keyword mapping for arXiv categories
MATH_KEYWORD_MAP = {
    # 基础数学
    "数论": ("number theory", "math.NT"),
    "代数": ("algebra", "math.RA"),
    "几何": ("geometry", "math.DG"),
    "拓扑": ("topology", "math.AT"),
    "分析": ("analysis", "math.CA"),
    "组合": ("combinatorics", "math.CO"),
    # 应用数学
    "概率": ("probability", "math.PR"),
    "统计": ("statistics", "stat.TH"),
    "优化": ("optimization", "math.OC"),
    "数值": ("numerical", "math.NA"),
    # 计算机科学
    "机器学习": ("machine learning", "cs.LG"),
    "深度学习": ("deep learning", "cs.LG"),
    "神经网络": ("neural network", "cs.NE"),
    "算法": ("algorithm", "cs.DS"),
    "计算": ("computational", "cs.CE"),
    # 物理
    "量子": ("quantum", "quant-ph"),
    "相对论": ("relativity", "gr-qc"),
    "凝聚态": ("condensed matter", "cond-mat"),
    # 通用数学
    "傅里叶": ("fourier", "math.CA"),
    "微积分": ("calculus", "math.CA"),
    "导数": ("derivative", "math.CA"),
    "积分": ("integral", "math.CA"),
    "极限": ("limit", "math.CA"),
    "级数": ("series", "math.CA"),
    "矩阵": ("matrix", "math.RA"),
    "特征值": ("eigenvalue", "math.RA"),
    "向量": ("vector", "math.RA"),
    "线性代数": ("linear algebra", "math.RA"),
    "方程": ("equation", "math.AP"),
    "函数": ("function", "math.CA"),
    "多项式": ("polynomial", "math.RA"),
    "勾股定理": ("pythagorean theorem", "math.HO"),
    "三角函数": ("trigonometry", "math.HO"),
    "实分析": ("real analysis", "math.CA"),
    "复分析": ("complex analysis", "math.CV"),
    "泛函分析": ("functional analysis", "math.FA"),
    "微分方程": ("differential equation", "math.AP"),
    "偏微分方程": ("partial differential", "math.AP"),
    "图论": ("graph theory", "math.CO"),
    "群论": ("group theory", "math.GR"),
    "环论": ("ring theory", "math.RA"),
    "域论": ("field theory", "math.RA"),
    "随机过程": ("stochastic process", "math.PR"),
    "马尔可夫": ("markov", "math.PR"),
    "贝叶斯": ("bayesian", "stat.TH"),
}


class LiteratureSearcher:
    """Enhanced academic literature searcher."""

    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    CROSSREF_API_URL = "https://api.crossref.org/works"

    def __init__(self):
        self._cache = {}

    def search(
        self,
        query: str,
        max_results: int = 10,
        sources: Optional[list] = None,
        categories: Optional[list] = None,
    ) -> list:
        """Search multiple academic sources.

        Args:
            query: Search query (Chinese or English)
            max_results: Maximum results per source
            sources: List of sources to search (default: ["arxiv", "crossref"])
            categories: arXiv categories to limit search

        Returns:
            List of paper dictionaries with metadata
        """
        if sources is None:
            sources = ["arxiv"]

        all_papers = []

        if "arxiv" in sources:
            arxiv_papers = self._search_arxiv(query, max_results, categories)
            all_papers.extend(arxiv_papers)

        if "crossref" in sources:
            crossref_papers = self._search_crossref(query, max_results)
            all_papers.extend(crossref_papers)

        # Deduplicate by title similarity
        all_papers = self._deduplicate(all_papers)

        # Sort by relevance (arXiv first, then by date)
        all_papers.sort(
            key=lambda p: (
                0 if p.get("source") == "arXiv" else 1,
                p.get("published", ""),
            ),
            reverse=True,
        )

        return all_papers[: max_results * 2]

    def _search_arxiv(
        self, query: str, max_results: int = 10, categories: Optional[list] = None
    ) -> list:
        """Search arXiv API with enhanced query processing."""
        search_query = self._build_arxiv_query(query, categories)
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(max_results, 50),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        url = f"{self.ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "JiuZhang/1.0 (Mathematics Research Platform; https://github.com/cycleuser/JiuZhang)"
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                xml_data = response.read().decode("utf-8")
            return self._parse_arxiv_response(xml_data)
        except Exception as e:
            return []

    def _build_arxiv_query(self, query: str, categories: Optional[list] = None) -> str:
        """Build an optimized arXiv search query."""
        # Check for known mathematical keywords
        for cn_keyword, (en_keyword, category) in MATH_KEYWORD_MAP.items():
            if cn_keyword in query:
                if categories:
                    cat_query = " OR ".join(f"cat:{c}" for c in categories)
                    return f"(all:{en_keyword}) AND ({cat_query})"
                return f"all:{en_keyword}"

        # For English queries, try direct search
        if any(c.isascii() for c in query):
            terms = query.split()
            if len(terms) <= 3:
                return f"all:{' AND '.join(terms)}"
            return f"all:{query}"

        # Fallback: use the query as-is
        return f"all:{query}"

    def _search_crossref(self, query: str, max_results: int = 10) -> list:
        """Search CrossRef API for DOI-registered papers."""
        params = {
            "query": query,
            "select": "title,author,abstract,DOI,url,published-print,published-online,type",
            "rows": min(max_results, 20),
            "sort": "relevance",
        }

        url = f"{self.CROSSREF_API_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JiuZhang/1.0 (mailto:research@jiuzhang.org)"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            papers = []
            items = data.get("message", {}).get("items", [])
            for item in items:
                title = item.get("title", [""])[0] if item.get("title") else ""
                authors = []
                for author in item.get("author", []):
                    name_parts = [author.get("given", ""), author.get("family", "")]
                    authors.append(" ".join(p for p in name_parts if p))

                pub_date = ""
                if item.get("published-print"):
                    pub_date = item["published-print"].get("date-parts", [[0]])[0][0]
                elif item.get("published-online"):
                    pub_date = item["published-online"].get("date-parts", [[0]])[0][0]

                papers.append(
                    {
                        "title": title,
                        "authors": ", ".join(authors[:5]),
                        "summary": item.get("abstract", "No abstract available"),
                        "url": item.get("URL", item.get("url", "")),
                        "published": str(pub_date) if pub_date else "",
                        "source": "CrossRef",
                        "doi": item.get("DOI", ""),
                        "type": item.get("type", "journal-article"),
                    }
                )
            return papers
        except Exception as e:
            import logging
            logging.warning(f"Error in search_literature: {e}")
            return []

    def _parse_arxiv_response(self, xml_data: str) -> list:
        """Parse arXiv API XML response with enhanced extraction."""
        papers = []
        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        try:
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry", namespace)

            for entry in entries:
                title_elem = entry.find("atom:title", namespace)
                summary_elem = entry.find("atom:summary", namespace)
                published_elem = entry.find("atom:published", namespace)
                id_elem = entry.find("atom:id", namespace)
                authors = entry.findall("atom:author", namespace)
                categories = entry.findall("atom:category", namespace)
                pdf_link = entry.find(
                    'atom:link[@title="pdf"]',
                    namespace,
                )

                title = (
                    title_elem.text.strip().replace("\n", " ").replace("  ", " ")
                    if title_elem is not None
                    else ""
                )
                summary = (
                    summary_elem.text.strip().replace("\n", " ")
                    if summary_elem is not None
                    else ""
                )
                published = published_elem.text if published_elem is not None else ""
                url = id_elem.text if id_elem is not None else ""
                pdf_url = pdf_link.get("href", "") if pdf_link is not None else ""

                author_names = []
                for author in authors:
                    name_elem = author.find("atom:name", namespace)
                    if name_elem is not None:
                        author_names.append(name_elem.text)

                cat_terms = []
                for cat in categories:
                    term = cat.get("term", "")
                    if term:
                        cat_terms.append(term)

                papers.append(
                    {
                        "title": title,
                        "authors": ", ".join(author_names[:5]),
                        "summary": summary[:1000]
                        + ("..." if len(summary) > 1000 else ""),
                        "url": url,
                        "pdf_url": pdf_url,
                        "published": published[:10] if published else "",
                        "source": "arXiv",
                        "categories": cat_terms,
                        "doi": "",
                    }
                )
        except ET.ParseError:
            pass

        return papers

    def _deduplicate(self, papers: list) -> list:
        """Remove duplicate papers based on title similarity."""
        seen_titles = set()
        unique_papers = []

        for paper in papers:
            title = paper.get("title", "").lower().strip()
            # Normalize title for comparison
            normalized = "".join(c for c in title if c.isalnum() or c.isspace())

            if normalized not in seen_titles and len(normalized) > 10:
                seen_titles.add(normalized)
                unique_papers.append(paper)

        return unique_papers

    def generate_review(self, papers: list, language: str = "zh") -> str:
        """Generate a comprehensive literature review."""
        if not papers or not papers[0].get("title"):
            return (
                "未找到相关文献。建议尝试不同的关键词或使用英文搜索。"
                if language == "zh"
                else "No relevant papers found. Try different keywords or search in English."
            )

        parts = []
        if language == "zh":
            parts.append("# 文献综述\n")
            parts.append(f"共检索到 {len(papers)} 篇相关文献，以下按来源分类介绍。\n")

            # Group by source
            arxiv_papers = [p for p in papers if p.get("source") == "arXiv"]
            crossref_papers = [p for p in papers if p.get("source") == "CrossRef"]

            if arxiv_papers:
                parts.append(f"\n## arXiv 预印本\n")
                parts.append(f"共 {len(arxiv_papers)} 篇。\n\n")
                for i, paper in enumerate(arxiv_papers, 1):
                    parts.append(self._format_paper_cn(paper, i))

            if crossref_papers:
                parts.append(f"\n## 正式出版物\n")
                parts.append(f"共 {len(crossref_papers)} 篇。\n\n")
                for i, paper in enumerate(crossref_papers, 1):
                    parts.append(self._format_paper_cn(paper, i + len(arxiv_papers)))

            # Summary analysis
            parts.append("\n## 研究趋势\n")
            years = [p.get("published", "")[:4] for p in papers if p.get("published")]
            if years:
                year_counts = {}
                for y in years:
                    if y and y.isdigit():
                        year_counts[y] = year_counts.get(y, 0) + 1
                parts.append("从发表年份来看，")
                year_parts = []
                for year in sorted(year_counts.keys()):
                    year_parts.append(f"{year}年{year_counts[year]}篇")
                parts.append("、".join(year_parts))
                parts.append("。可见该领域近年来持续受到关注。\n")

        else:
            parts.append("# Literature Review\n")
            parts.append(f"Found {len(papers)} relevant papers.\n")

            for i, paper in enumerate(papers, 1):
                parts.append(self._format_paper_en(paper, i))

        return "\n".join(parts)

    def _format_paper_cn(self, paper: dict, index: int) -> str:
        """Format a single paper in Chinese."""
        title = paper.get("title", "Unknown")
        authors = paper.get("authors", "Unknown")
        published = paper.get("published", "Unknown")
        source = paper.get("source", "Unknown")
        summary = paper.get("summary", "No abstract")
        url = paper.get("url", "")
        pdf_url = paper.get("pdf_url", "")
        doi = paper.get("doi", "")
        cats = paper.get("categories", [])

        lines = [f"[{index}] {authors}. {title}. {source}, {published}.\n"]

        if cats:
            lines.append(f"分类：{', '.join(cats)}。\n")

        if doi:
            lines.append(f"DOI：{doi}。\n")

        if summary:
            lines.append(f"摘要：{summary}\n")

        if url:
            lines.append(f"链接：{url}\n")

        if pdf_url:
            lines.append(f"PDF：{pdf_url}\n")

        lines.append("\n")
        return "\n".join(lines)

    def _format_paper_en(self, paper: dict, index: int) -> str:
        """Format a single paper in English."""
        title = paper.get("title", "Unknown")
        authors = paper.get("authors", "Unknown")
        published = paper.get("published", "Unknown")
        source = paper.get("source", "Unknown")
        summary = paper.get("summary", "No abstract")
        url = paper.get("url", "")
        doi = paper.get("doi", "")

        lines = [f"[{index}] {authors}. {title}. {source}, {published}.\n"]

        if doi:
            lines.append(f"DOI: {doi}.\n")

        if summary:
            lines.append(f"Abstract: {summary}\n")

        if url:
            lines.append(f"Link: {url}\n")

        lines.append("\n")
        return "\n".join(lines)
