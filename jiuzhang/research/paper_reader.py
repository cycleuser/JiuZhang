"""Paper Reader and Summarizer for JiuZhang.

Parses arXiv papers, extracts key information, and generates summaries.
"""

import json
import urllib.request
import urllib.parse
from typing import Optional
from datetime import datetime


class PaperReader:
    """Reads and summarizes academic papers from arXiv."""

    ARXIV_API_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self._cache = {}

    def fetch_paper(self, arxiv_id: str) -> Optional[dict]:
        """Fetch a paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2401.12345" or "math/0501234")

        Returns:
            Paper dictionary with metadata and abstract
        """
        if arxiv_id in self._cache:
            return self._cache[arxiv_id]

        # Format the ID for API
        search_id = arxiv_id
        if not arxiv_id.startswith("arxiv:"):
            if "/" in arxiv_id:
                search_id = f"id:{arxiv_id}"
            else:
                search_id = f"id:{arxiv_id}"

        params = {
            "id_list": arxiv_id,
            "max_results": 1,
        }

        url = f"{self.ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JiuZhang/1.0 (Mathematics Research Platform)"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                xml_data = response.read().decode("utf-8")

            paper = self._parse_single_paper(xml_data)
            if paper:
                self._cache[arxiv_id] = paper
            return paper
        except Exception as e:
            return {"error": str(e)}

    def _parse_single_paper(self, xml_data: str) -> Optional[dict]:
        """Parse a single paper from arXiv XML."""
        import xml.etree.ElementTree as ET

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        try:
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry", namespace)

            if not entries:
                return None

            entry = entries[0]

            title_elem = entry.find("atom:title", namespace)
            summary_elem = entry.find("atom:summary", namespace)
            published_elem = entry.find("atom:published", namespace)
            updated_elem = entry.find("atom:updated", namespace)
            id_elem = entry.find("atom:id", namespace)
            authors = entry.findall("atom:author", namespace)
            categories = entry.findall("atom:category", namespace)
            links = entry.findall("atom:link", namespace)
            comment_elem = entry.find("arxiv:comment", namespace)
            doi_elem = entry.find("arxiv:doi", namespace)
            journal_ref_elem = entry.find("arxiv:journal_ref", namespace)

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
            published = published_elem.text[:10] if published_elem is not None else ""
            updated = updated_elem.text[:10] if updated_elem is not None else ""
            url = id_elem.text if id_elem is not None else ""
            comment = comment_elem.text.strip() if comment_elem is not None else ""
            doi = doi_elem.text if doi_elem is not None else ""
            journal_ref = journal_ref_elem.text if journal_ref_elem is not None else ""

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

            pdf_url = ""
            abs_url = url
            for link in links:
                title_attr = link.get("title", "")
                if title_attr == "pdf":
                    pdf_url = link.get("href", "")
                elif link.get("type") == "text/html":
                    abs_url = link.get("href", url)

            return {
                "arxiv_id": url.split("/abs/")[-1] if "/abs/" in url else "",
                "title": title,
                "authors": author_names,
                "authors_str": ", ".join(author_names[:10]),
                "abstract": summary,
                "published": published,
                "updated": updated,
                "categories": cat_terms,
                "url": url,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
                "doi": doi,
                "journal_ref": journal_ref,
            }
        except Exception as e:
            import logging
            logging.warning(f"Error parsing paper metadata: {e}")
            return None

    def generate_summary(self, paper: dict, language: str = "zh") -> str:
        """Generate a structured summary of a paper.

        Args:
            paper: Paper dictionary
            language: Output language

        Returns:
            Structured summary
        """
        if not paper or "error" in paper:
            return (
                "无法获取论文信息"
                if language == "zh"
                else "Failed to fetch paper information"
            )

        parts = []

        if language == "zh":
            parts.append(f"# 论文摘要\n")
            parts.append(f"\n## {paper.get('title', 'Unknown')}\n")
            parts.append(f"\n**作者**: {paper.get('authors_str', 'Unknown')}\n")
            parts.append(f"\n**发表时间**: {paper.get('published', 'Unknown')}\n")
            parts.append(f"\n**分类**: {', '.join(paper.get('categories', []))}\n")

            if paper.get("comment"):
                parts.append(f"\n**备注**: {paper.get('comment')}\n")

            if paper.get("journal_ref"):
                parts.append(f"\n**期刊**: {paper.get('journal_ref')}\n")

            parts.append(f"\n## 摘要\n\n{paper.get('abstract', 'No abstract')}\n")

            parts.append(f"\n## 链接\n")
            parts.append(f"- arXiv: {paper.get('abs_url', '')}\n")
            if paper.get("pdf_url"):
                parts.append(f"- PDF: {paper.get('pdf_url')}\n")
            if paper.get("doi"):
                parts.append(f"- DOI: {paper.get('doi')}\n")

            # Key information extraction
            abstract = paper.get("abstract", "").lower()
            parts.append(f"\n## 关键信息提取\n")

            # Detect methods
            methods = []
            if "proof" in abstract or "prove" in abstract:
                methods.append("包含证明")
            if "theorem" in abstract or "conjecture" in abstract:
                methods.append("涉及定理/猜想")
            if "algorithm" in abstract or "compute" in abstract:
                methods.append("包含算法")
            if "classif" in abstract:
                methods.append("分类问题")
            if "bound" in abstract or "estimate" in abstract:
                methods.append("估计/界")
            if "construct" in abstract:
                methods.append("构造性结果")

            if methods:
                parts.append(f"\n**研究方法**: {', '.join(methods)}\n")

            # Detect field
            categories = paper.get("categories", [])
            field_map = {
                "math.AG": "代数几何",
                "math.NT": "数论",
                "math.DG": "微分几何",
                "math.GT": "几何拓扑",
                "math.RT": "表示论",
                "math.CT": "范畴论",
                "math.AT": "代数拓扑",
                "math.AP": "偏微分方程",
                "math.PR": "概率论",
                "math.FA": "泛函分析",
                "math.OA": "算子代数",
                "math.QA": "量子代数",
                "math.SG": "辛几何",
                "math.DS": "动力系统",
                "math.LO": "数理逻辑",
                "math.CO": "组合学",
                "math.NA": "数值分析",
                "math.OC": "优化",
            }
            fields = [field_map.get(c, c) for c in categories]
            if fields:
                parts.append(f"\n**研究领域**: {', '.join(fields)}\n")

        else:
            parts.append(f"# Paper Summary\n")
            parts.append(f"\n## {paper.get('title', 'Unknown')}\n")
            parts.append(f"\n**Authors**: {paper.get('authors_str', 'Unknown')}\n")
            parts.append(f"\n**Published**: {paper.get('published', 'Unknown')}\n")
            parts.append(
                f"\n**Categories**: {', '.join(paper.get('categories', []))}\n"
            )

            if paper.get("comment"):
                parts.append(f"\n**Comments**: {paper.get('comment')}\n")

            if paper.get("journal_ref"):
                parts.append(f"\n**Journal**: {paper.get('journal_ref')}\n")

            parts.append(f"\n## Abstract\n\n{paper.get('abstract', 'No abstract')}\n")

            parts.append(f"\n## Links\n")
            parts.append(f"- arXiv: {paper.get('abs_url', '')}\n")
            if paper.get("pdf_url"):
                parts.append(f"- PDF: {paper.get('pdf_url')}\n")
            if paper.get("doi"):
                parts.append(f"- DOI: {paper.get('doi')}\n")

        return "\n".join(parts)

    def fetch_and_summarize(self, arxiv_id: str, language: str = "zh") -> str:
        """Fetch a paper and generate summary.

        Args:
            arxiv_id: arXiv ID
            language: Output language

        Returns:
            Structured summary
        """
        paper = self.fetch_paper(arxiv_id)
        return self.generate_summary(paper, language)

    def fetch_multiple(self, arxiv_ids: list) -> list:
        """Fetch multiple papers.

        Args:
            arxiv_ids: List of arXiv IDs

        Returns:
            List of paper dictionaries
        """
        papers = []
        for arxiv_id in arxiv_ids:
            paper = self.fetch_paper(arxiv_id)
            if paper:
                papers.append(paper)
        return papers
