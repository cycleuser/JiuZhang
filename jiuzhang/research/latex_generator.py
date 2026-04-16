"""LaTeX Paper Generator for JiuZhang.

Generates properly formatted LaTeX research papers from research results.
"""

from typing import Optional
from datetime import datetime
from pathlib import Path


class LaTeXPaperGenerator:
    """Generates LaTeX research papers."""

    TEMPLATE = r"""\documentclass[12pt,a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{booktabs}
\usepackage{tikz}
\usepackage{biblatex}

\geometry{margin=1in}

% Theorem environments
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{conjecture}[theorem]{Conjecture}

\title{{JZ_TITLE}}
\author{{JZ_AUTHOR}}
\date{{JZ_DATE}}

\begin{{document}}

\maketitle

\begin{{abstract}}
JZ_ABSTRACT
\end{{abstract}}

\tableofcontents
\newpage

JZ_SECTIONS

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
"""

    @staticmethod
    def generate_paper(
        title: str,
        author: str,
        abstract: str,
        sections: list,
        references: Optional[list] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a LaTeX paper.

        Args:
            title: Paper title
            author: Author name
            abstract: Abstract text
            sections: List of section dictionaries with 'title' and 'content'
            references: List of references
            output_path: Output file path

        Returns:
            LaTeX source code
        """
        sections_latex = []
        for section in sections:
            sec_title = section.get("title", "")
            sec_content = section.get("content", "")
            sec_level = section.get("level", "section")

            if sec_level == "section":
                sections_latex.append(f"\n\\section{{{sec_title}}}\n\n{sec_content}\n")
            elif sec_level == "subsection":
                sections_latex.append(
                    f"\n\\subsection{{{sec_title}}}\n\n{sec_content}\n"
                )
            elif sec_level == "subsubsection":
                sections_latex.append(
                    f"\n\\subsubsection{{{sec_title}}}\n\n{sec_content}\n"
                )

        sections_str = "\n".join(sections_latex)

        latex = LaTeXPaperGenerator.TEMPLATE
        latex = latex.replace("JZ_TITLE", title)
        latex = latex.replace("JZ_AUTHOR", author)
        latex = latex.replace("JZ_DATE", datetime.now().strftime("%B %d, %Y"))
        latex = latex.replace("JZ_ABSTRACT", abstract)
        latex = latex.replace("JZ_SECTIONS", sections_str)

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(latex)

        return latex

    @staticmethod
    def generate_from_research(
        research_result,
        author: str = "JiuZhang Research Assistant",
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a LaTeX paper from a research result.

        Args:
            research_result: ResearchResult object
            author: Author name
            output_path: Output file path

        Returns:
            LaTeX source code
        """
        title = f"Research Report: {research_result.topic}"
        abstract = (
            research_result.summary[:500]
            if research_result.summary
            else "This paper presents a comprehensive study of the topic."
        )

        sections = []

        # Introduction
        if research_result.summary:
            sections.append(
                {
                    "title": "Introduction",
                    "content": research_result.summary,
                    "level": "section",
                }
            )

        # Literature Review
        if research_result.literature_review:
            sections.append(
                {
                    "title": "Literature Review",
                    "content": research_result.literature_review,
                    "level": "section",
                }
            )

        # Mathematical Derivation
        if research_result.mathematical_derivation:
            sections.append(
                {
                    "title": "Mathematical Derivation",
                    "content": research_result.mathematical_derivation,
                    "level": "section",
                }
            )

        # Experiments
        if research_result.experiments:
            exp_content = ""
            for i, exp in enumerate(research_result.experiments, 1):
                exp_content += (
                    f"\n\\subsection{{Experiment {i}: {exp.get('title', '')}}}\n\n"
                )
                exp_content += f"{exp.get('description', '')}\n\n"
                if exp.get("code"):
                    exp_content += "\\begin{verbatim}\n"
                    exp_content += exp["code"][:2000] + "\n"
                    exp_content += "\\end{verbatim}\n\n"
            sections.append(
                {"title": "Experiments", "content": exp_content, "level": "section"}
            )

        # References
        if research_result.references:
            ref_content = "\\begin{thebibliography}{99}\n\n"
            for i, ref in enumerate(research_result.references, 1):
                authors = ref.get("authors", "Unknown")
                title = ref.get("title", "Unknown")
                year = ref.get("published", "")[:4] if ref.get("published") else "n.d."
                url = ref.get("url", "")
                ref_content += f"\\bibitem{{ref{i}}} {authors}. ``{title}.'' {year}. "
                if url:
                    ref_content += f"\\url{{{url}}}."
                ref_content += "\n\n"
            ref_content += "\\end{thebibliography}\n"
            sections.append(
                {"title": "References", "content": ref_content, "level": "section"}
            )

        return LaTeXPaperGenerator.generate_paper(
            title=title,
            author=author,
            abstract=abstract,
            sections=sections,
            output_path=output_path,
        )

    @staticmethod
    def generate_beamer_presentation(
        title: str, author: str, slides: list, output_path: Optional[str] = None
    ) -> str:
        """Generate a Beamer presentation.

        Args:
            title: Presentation title
            author: Author name
            slides: List of slide dictionaries with 'title' and 'content'
            output_path: Output file path

        Returns:
            LaTeX Beamer source code
        """
        beamer_template = r"""\documentclass[12pt]{beamer}

\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{tikz}

\usetheme{Madrid}
\usecolortheme{default}

\title{JZ_B_TITLE}
\author{JZ_B_AUTHOR}
\date{\today}

\begin{document}

\begin{frame}
\titlepage
\end{frame}

\begin{frame}{Outline}
\tableofcontents
\end{frame}

JZ_B_SLIDES

\end{document}
"""

        slides_latex = []
        for slide in slides:
            slide_title = slide.get("title", "")
            slide_content = slide.get("content", "")
            slide_layout = slide.get("layout", "default")

            if slide_layout == "two_columns":
                left = slide.get("left", "")
                right = slide.get("right", "")
                slides_latex.append(f"""
\\begin{{frame}}{{{slide_title}}}
\\begin{{columns}}
\\begin{{column}}{{0.48\\textwidth}}
{left}
\\end{{column}}
\\begin{{column}}{{0.48\\textwidth}}
{right}
\\end{{column}}
\\end{{columns}}
\\end{{frame}}
""")
            else:
                slides_latex.append(f"""
\\begin{{frame}}{{{slide_title}}}
{slide_content}
\\end{{frame}}
""")

        slides_str = "\n".join(slides_latex)

        latex = beamer_template
        latex = latex.replace("JZ_B_TITLE", title)
        latex = latex.replace("JZ_B_AUTHOR", author)
        latex = latex.replace("JZ_B_SLIDES", slides_str)

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(latex)

        return latex
