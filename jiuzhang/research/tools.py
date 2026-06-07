"""New Research Tools for JiuZhang — extended capabilities beyond basic math.

Adds:
- web_search: DuckDuckGo/Google search for recent math results
- wolfram_query: Wolfram Alpha API integration
- oeis_lookup: Online Encyclopedia of Integer Sequences
- lean_check: Verify statements in Lean 4 proof assistant
- sage_compute: SageMath for advanced algebra/number theory
- data_analysis: pandas/numpy for experimental math data
- paper_download: Fetch and parse arXiv/DOI papers
- math_stackexchange: Search MathOverflow/StackExchange
"""

from dataclasses import dataclass
from typing import Optional, Any
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path


# ── Web Search ───────────────────────────────────────────────────────

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


def web_search(query: str, max_results: int = 5) -> list:
    """Search the web for mathematical content using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum results to return

    Returns:
        List of SearchResult objects
    """
    results = []

    try:
        # Use DuckDuckGo HTML search (no API key needed)
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JiuZhang-Math-Research/1.0"},
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")

        # Extract results from HTML
        result_blocks = re.findall(
            r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>',
            html,
        )
        snippet_blocks = re.findall(
            r'<a class="result__snippet"[^>]*>([^<]+(?:<[^/][^>]*>[^<]*</[^>]*>)*[^<]*)</a>',
            html,
        )

        for i, (url, title) in enumerate(result_blocks[:max_results]):
            snippet = ""
            if i < len(snippet_blocks):
                snippet = re.sub(r'<[^>]+>', '', snippet_blocks[i])
            results.append(SearchResult(
                title=title.strip(),
                url=url,
                snippet=snippet.strip(),
                source="duckduckgo",
            ))

    except Exception as e:
        results.append(SearchResult(
            title="Search Error",
            url="",
            snippet=f"Web search failed: {str(e)[:200]}",
            source="error",
        ))

    return results


# ── OEIS Lookup ──────────────────────────────────────────────────────

def oeis_lookup(sequence: list, max_results: int = 5) -> list:
    """Look up a sequence in the Online Encyclopedia of Integer Sequences.

    Args:
        sequence: List of integers (first few terms)
        max_results: Max results to return

    Returns:
        List of dicts with OEIS entry info
    """
    results = []

    try:
        seq_str = ",".join(str(n) for n in sequence[:20])
        url = f"https://oeis.org/search?q={seq_str}&fmt=json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JiuZhang-Math-Research/1.0"},
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for entry in data.get("results", [])[:max_results]:
            results.append({
                "id": f"A{entry.get('number', '')}",
                "name": entry.get("name", ""),
                "data": entry.get("data", ""),
                "formula": entry.get("formula", []),
                "comment": entry.get("comment", []),
                "references": entry.get("reference", []),
            })

    except Exception as e:
        results.append({"error": f"OEIS lookup failed: {str(e)[:200]}"})

    return results


# ── Wolfram Alpha Query ──────────────────────────────────────────────

def wolfram_query(query: str, app_id: Optional[str] = None) -> dict:
    """Query Wolfram Alpha for computational results.

    Args:
        query: Mathematical query
        app_id: Wolfram Alpha App ID (uses env var WOLFRAM_APP_ID if None)

    Returns:
        Dict with pod results
    """
    import os

    app_id = app_id or os.environ.get("WOLFRAM_APP_ID", "")
    if not app_id:
        return {"error": "No Wolfram Alpha App ID configured. Set WOLFRAM_APP_ID env var."}

    try:
        url = "https://api.wolframalpha.com/v2/query"
        params = urllib.parse.urlencode({
            "appid": app_id,
            "input": query,
            "format": "plaintext",
            "output": "json",
        })

        req = urllib.request.Request(
            f"{url}?{params}",
            headers={"User-Agent": "JiuZhang-Math-Research/1.0"},
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        pods = data.get("queryresult", {}).get("pods", [])
        results = {}
        for pod in pods:
            title = pod.get("title", "")
            for subpod in pod.get("subpods", []):
                text = subpod.get("plaintext", "")
                if text:
                    results[title] = text
                    break

        return {
            "success": data.get("queryresult", {}).get("success", False),
            "results": results,
        }

    except Exception as e:
        return {"error": f"Wolfram query failed: {str(e)[:200]}"}


# ── Math StackExchange Search ────────────────────────────────────────

def search_math_stackexchange(query: str, site: str = "math", max_results: int = 5) -> list:
    """Search Math StackExchange or MathOverflow.

    Args:
        query: Search query
        site: "math" for Math StackExchange, "mathoverflow" for MathOverflow
        max_results: Max results

    Returns:
        List of question dicts
    """
    results = []

    try:
        api_url = "https://api.stackexchange.com/2.3/search/advanced"
        params = urllib.parse.urlencode({
            "site": site,
            "q": query,
            "pagesize": max_results,
            "order": "desc",
            "sort": "relevance",
            "filter": "withbody",
        })

        req = urllib.request.Request(
            f"{api_url}?{params}",
            headers={"User-Agent": "JiuZhang-Math-Research/1.0"},
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "score": item.get("score", 0),
                "answer_count": item.get("answer_count", 0),
                "tags": item.get("tags", []),
                "excerpt": re.sub(r'<[^>]+>', '', item.get("body", "")[:300]),
            })

    except Exception as e:
        results.append({"error": f"StackExchange search failed: {str(e)[:200]}"})

    return results


# ── Lean 4 Proof Check ───────────────────────────────────────────────

def lean_check(statement: str, lean_code: str) -> dict:
    """Check a mathematical statement using Lean 4 proof assistant.

    Requires `lean` CLI to be installed and on PATH.

    Args:
        statement: Human-readable theorem statement
        lean_code: Lean 4 code to check (theorem + proof)

    Returns:
        Dict with check results
    """
    import subprocess
    import tempfile
    import os

    try:
        # Write Lean code to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lean", delete=False, encoding="utf-8"
        ) as f:
            f.write(lean_code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["lean", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "statement": statement,
                "passed": result.returncode == 0,
                "output": result.stdout[:500],
                "errors": result.stderr[:500] if result.returncode != 0 else "",
            }

        finally:
            os.unlink(temp_path)

    except FileNotFoundError:
        return {
            "statement": statement,
            "passed": None,
            "error": "Lean 4 not installed. Install from https://lean-lang.org/",
        }
    except Exception as e:
        return {
            "statement": statement,
            "passed": False,
            "error": f"Lean check failed: {str(e)[:200]}",
        }


# ── Data Analysis ────────────────────────────────────────────────────

def analyze_numeric_data(
    data: list,
    operation: str = "describe",
) -> dict:
    """Perform statistical analysis on numeric data.

    Args:
        data: List of numbers
        operation: "describe", "histogram", "fit", "correlation"

    Returns:
        Dict with analysis results
    """
    import numpy as np

    data = np.array(data, dtype=float)

    if operation == "describe":
        return {
            "count": len(data),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "median": float(np.median(data)),
            "q25": float(np.percentile(data, 25)),
            "q75": float(np.percentile(data, 75)),
        }

    elif operation == "histogram":
        hist, bins = np.histogram(data, bins=10)
        return {
            "histogram": hist.tolist(),
            "bin_edges": bins.tolist(),
        }

    elif operation == "fit":
        try:
            from scipy import stats
            # Try normal distribution fit
            mu, sigma = stats.norm.fit(data)
            ks_stat, ks_pvalue = stats.kstest(data, 'norm', args=(mu, sigma))
            return {
                "distribution": "normal",
                "mu": float(mu),
                "sigma": float(sigma),
                "ks_statistic": float(ks_stat),
                "ks_pvalue": float(ks_pvalue),
                "is_normal": ks_pvalue > 0.05,
            }
        except ImportError:
            return {"error": "scipy not available for distribution fitting"}

    return {"error": f"Unknown operation: {operation}"}


# ── Paper Download ───────────────────────────────────────────────────

def fetch_arxiv_paper(arxiv_id: str) -> dict:
    """Fetch an arXiv paper by ID and extract metadata + abstract.

    Args:
        arxiv_id: arXiv ID (e.g., "2401.12345")

    Returns:
        Dict with paper metadata
    """
    try:
        url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JiuZhang-Math-Research/1.0"},
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")

        root = ET.fromstring(data)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        entry = root.find("atom:entry", ns)
        if entry is None:
            return {"error": f"No paper found with ID: {arxiv_id}"}

        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        authors = entry.findall("atom:author/atom:name", ns)
        published = entry.find("atom:published", ns)
        categories = entry.findall("atom:category", ns)
        pdf_link = entry.find('atom:link[@title="pdf"]', ns)

        return {
            "id": arxiv_id,
            "title": title.text.strip() if title is not None and title.text else "",
            "authors": [a.text.strip() for a in authors if a.text],
            "summary": summary.text.strip()[:500] if summary is not None and summary.text else "",
            "published": published.text if published is not None else "",
            "categories": [c.get("term", "") for c in categories],
            "pdf_url": pdf_link.get("href", "") if pdf_link is not None else "",
        }

    except Exception as e:
        return {"error": f"arXiv fetch failed: {str(e)[:200]}"}


# ── Utility: execute all relevant searches at once ───────────────────

def multi_search(query: str, sequence: Optional[list] = None) -> dict:
    """Run multiple search tools in parallel for a comprehensive lookup.

    Args:
        query: Math search query
        sequence: Optional integer sequence for OEIS lookup

    Returns:
        Dict with all search results
    """
    results = {
        "query": query,
        "web": [],
        "stackexchange": [],
        "arxiv": None,
        "oeis": [],
    }

    # Web search
    try:
        results["web"] = [{"title": r.title, "url": r.url, "snippet": r.snippet}
                          for r in web_search(query)]
    except Exception:
        pass

    # StackExchange
    try:
        results["stackexchange"] = search_math_stackexchange(query)
    except Exception:
        pass

    # arXiv (if query matches an ID pattern)
    arxiv_match = re.search(r'(?:arxiv[:\s]*)?(\d{4}\.\d{4,5})', query)
    if arxiv_match:
        try:
            results["arxiv"] = fetch_arxiv_paper(arxiv_match.group(1))
        except Exception:
            pass

    # OEIS
    if sequence:
        try:
            results["oeis"] = oeis_lookup(sequence)
        except Exception:
            pass

    return results
