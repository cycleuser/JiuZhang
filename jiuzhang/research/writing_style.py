"""Writing style guidelines and prompt templates for JiuZhang.

Ensures all AI-generated content:
1. Has strict reference citations
2. Reads naturally like human academic writing
3. Avoids AI patterns (bullet points, bold text, transition word stacking)
4. Uses proper academic prose style
"""

# Core writing principles
WRITING_PRINCIPLES = """
写作原则：
1. 使用连贯的段落式写作，避免分点列举
2. 不使用加粗、星号等强调标记
3. 避免使用"首先、然后、进而、最终、总之、综上所述"等过渡词堆砌
4. 引用必须标注具体出处，格式为 [作者，年份] 或 [文献编号]
5. 数学公式使用 LaTeX 格式，嵌入段落中自然呈现
6. 语言风格应像数学教科书或学术论文，严谨但不生硬
7. 每个重要结论都必须有推导过程或文献支持
8. 避免空泛的总结性语句，用具体内容代替
"""

# Prompt template for mathematical derivation
DERIVATION_PROMPT = """请对以下数学主题进行学术性的深入推导：

主题：{topic}
语言：{lang}
深度：{depth}

写作要求：
{principles}

请按学术论文的方式组织内容，包含以下部分（使用自然段落，不要分点）：

引言部分：介绍该主题的历史背景和数学意义，引用相关文献说明其重要性。

定义与预备知识：给出所有必要的数学定义，每个定义后标注来源文献。

主要推导：逐步展开推导过程，每一步都要说明依据的定理或引理，并标注出处。重要的中间结果要单独成段。

定理与证明：如果有重要定理，给出完整陈述和证明过程，证明中每一步都要有明确依据。

应用与例子：给出 2-3 个具体例子说明理论的应用，例子要有实际数学意义。

参考文献：在文末列出所有引用的文献，格式为 [编号] 作者。文献名。期刊/出版社，年份。

注意：全文使用连贯的学术散文风格，像数学专著中的章节，不要使用列表、加粗或项目符号。"""

# Prompt template for literature review
LITERATURE_PROMPT = """请撰写关于以下主题的学术文献综述：

主题：{topic}
语言：{lang}

写作要求：
{principles}

请按以下方式组织：

开篇介绍该研究领域的整体概况和发展脉络，引用开创性文献说明领域起源。

按时间或主题线索梳理重要文献，每篇文献都要说明其贡献和局限，并标注具体出处。文献之间要有逻辑关联，形成连贯的学术叙事。

讨论当前研究的前沿方向和未解决的问题，引用最新文献支持论点。

文末列出所有引用的文献，格式规范。

注意：使用学术综述的标准写法，段落之间自然过渡，不要使用分点或加粗。"""

# Prompt template for research report
RESEARCH_PROMPT = """请撰写关于以下数学主题的研究报告：

主题：{topic}
语言：{lang}
深度：{depth}

写作要求：
{principles}

报告应包含：

研究背景：介绍该主题的数学背景和重要性，引用经典文献。

理论框架：建立研究的理论基础，所有定义和定理都要有文献支持。

主要结果：呈现研究的核心发现，每个结果都要有完整的推导或证明过程。

讨论：分析结果的意义和局限，与前人工作对比，引用相关文献。

参考文献：列出所有引用，格式为 [编号] 作者。文献名。出处，年份。

注意：全文采用数学论文的标准写法，使用连贯的学术语言，避免任何列表、加粗或 AI 风格的过渡词。"""

# Prompt template for frontier mathematics
FRONTIER_PROMPT = """请对以下前沿数学主题进行学术性分析：

主题：{topic}
语言：{lang}

写作要求：
{principles}

请包含以下内容：

该主题在数学中的位置和与其他领域的联系，引用关键文献说明其发展脉络。

核心概念和主要定理的阐述，每个重要结果都要标注出处。

当前研究的热点和开放问题，引用最新研究论文。

可能的研究方向和方法论讨论。

参考文献列表。

注意：像数学综述文章那样写作，使用专业但流畅的学术语言，段落自然衔接，不使用分点或强调标记。"""

# Prompt template for open problems
OPEN_PROBLEM_PROMPT = """请详细分析以下数学开放问题：

问题：{problem_name}
语言：{lang}

写作要求：
{principles}

请包含：

问题的历史起源和提出背景，引用原始文献。

问题的精确数学表述。

已知的部分结果和相关定理，每个都要标注出处。

研究该问题的主要方法和尝试，引用相关论文。

该问题与其他数学领域的联系。

为什么这个问题如此困难，技术障碍在哪里。

参考文献列表。

注意：使用数学史和数学论文的标准写法，连贯叙述，不使用列表或加粗。"""
