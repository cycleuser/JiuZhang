"""Mathematical Reasoning Prompt Templates for JiuZhang.

Specialized prompts optimized for mathematical reasoning, proof generation,
and symbolic computation.
"""

MATH_REASONING_PROMPTS = {
    "theorem_proof": {
        "zh": """请严格按照以下步骤证明该定理：

1. **前提条件**：明确列出所有假设和已知条件
2. **目标陈述**：清楚表述要证明的结论
3. **证明策略**：选择合适的证明方法（直接证明、反证法、归纳法等）
4. **详细论证**：每一步都要有依据，引用相关定理或引理
5. **逻辑连接**：使用恰当的逻辑连接词
6. **结论总结**：重申结论并指出证明完成

定理：{theorem}

请提供完整严谨的数学证明：""",
        "en": """Please prove this theorem following these steps:

1. **Given Conditions**: State all assumptions and known facts clearly
2. **Goal Statement**: Clearly state what needs to be proven
3. **Proof Strategy**: Choose appropriate method (direct proof, contradiction, induction, etc.)
4. **Detailed Argument**: Each step must have justification, citing relevant theorems or lemmas
5. **Logical Connections**: Use proper logical connectors
6. **Conclusion Summary**: Restate the conclusion and indicate proof completion

Theorem: {theorem}

Provide a complete and rigorous mathematical proof:"""
    },
    
    "problem_solving": {
        "zh": """请按照Polya解题法解决此数学问题：

**第一步：理解问题**
- 求解什么？
- 已知条件是什么？
- 是否有足够的信息？

**第二步：制定计划**
- 是否见过类似问题？
- 能否使用已知定理或公式？
- 需要引入辅助元素吗？

**第三步：执行计划**
- 详细展示每一步计算
- 验证每个推理步骤
- 使用正确的数学符号

**第四步：回顾检验**
- 结果合理吗？
- 能否用其他方法验证？
- 是否可以推广？

问题：{problem}

请完整解答：""",
        "en": """Solve this mathematical problem using Polya's problem-solving method:

**Step 1: Understand the Problem**
- What is being asked?
- What are the given conditions?
- Is there sufficient information?

**Step 2: Devise a Plan**
- Have you seen a similar problem?
- Can you apply known theorems or formulas?
- Do you need auxiliary elements?

**Step 3: Carry Out the Plan**
- Show each calculation step in detail
- Verify each reasoning step
- Use proper mathematical notation

**Step 4: Look Back and Check**
- Does the result make sense?
- Can you verify using another method?
- Can this be generalized?

Problem: {problem}

Please provide a complete solution:"""
    },
    
    "symbolic_computation": {
        "zh": """请使用符号计算方法解决此问题。要求：

1. **变量定义**：明确定义所有变量及其域
2. **表达式构建**：写出准确的数学表达式
3. **符号操作**：使用代数规则进行变形
4. **验证检查**：验证中间步骤的正确性
5. **最终结果**：给出最简形式的答案

计算：{computation}

注意：如果涉及Python代码，请使用SymPy库的语法。

请提供详细步骤：""",
        "en": """Solve this using symbolic computation methods. Requirements:

1. **Variable Definition**: Clearly define all variables and their domains
2. **Expression Construction**: Write accurate mathematical expressions
3. **Symbolic Manipulation**: Apply algebraic rules for transformation
4. **Verification Check**: Verify correctness of intermediate steps
5. **Final Result**: Give answer in simplest form

Computation: {computation}

Note: If Python code is involved, please use SymPy library syntax.

Provide detailed steps:"""
    },
    
    "conjecture_analysis": {
        "zh": """请分析这个数学猜想：

**背景研究**
- 相关的已有结果
- 猜想的历史和意义
- 已知的特殊情况

**证据收集**
- 小规模验证
- 特殊情形检验
- 数值证据分析

**障碍分析**
- 为何难以证明
- 主要技术困难
- 相关的研究进展

**潜在途径**
- 可能的证明思路
- 需要的预备知识
- 相关的开放问题

猜想：{conjecture}

请进行深入分析：""",
        "en": """Analyze this mathematical conjecture:

**Background Research**
- Related existing results
- History and significance of the conjecture
- Known special cases

**Evidence Collection**
- Small-scale verification
- Special case examination
- Numerical evidence analysis

**Obstacle Analysis**
- Why it's difficult to prove
- Main technical challenges
- Related research progress

**Potential Approaches**
- Possible proof strategies
- Required preliminary knowledge
- Related open problems

Conjecture: {conjecture}

Please provide in-depth analysis:"""
    },
    
    "mathematical_modeling": {
        "zh": """请建立数学模型解决此实际问题：

**问题抽象**
- 识别关键变量
- 确定约束条件
- 明确目标函数

**模型构建**
- 建立方程组
- 确定参数范围
- 考虑边界条件

**模型分析**
- 解的存在性和唯一性
- 模型的合理性检验
- 敏感性分析

**求解与验证**
- 求解方法选择
- 数值求解
- 结果验证

实际问题：{problem}

请构建并分析数学模型：""",
        "en": """Build a mathematical model to solve this real-world problem:

**Problem Abstraction**
- Identify key variables
- Determine constraint conditions
- Clarify objective function

**Model Construction**
- Establish equation system
- Determine parameter ranges
- Consider boundary conditions

**Model Analysis**
- Existence and uniqueness of solutions
- Model validity check
- Sensitivity analysis

**Solution and Verification**
- Solution method selection
- Numerical solution
- Result verification

Real-world problem: {problem}

Please construct and analyze the mathematical model:"""
    }
}

MATH_KNOWLEDGE_BASE = {
    "theorems": {
        "pythagorean": {
            "name": "Pythagorean Theorem",
            "name_cn": "勾股定理",
            "statement": "In a right triangle, a² + b² = c² where c is the hypotenuse",
            "statement_cn": "在直角三角形中，a² + b² = c²，其中c是斜边",
            "conditions": "Triangle must be right-angled",
            "applications": ["Geometry", "Trigonometry", "Distance calculations"]
        },
        "fundamental_calc": {
            "name": "Fundamental Theorem of Calculus",
            "name_cn": "微积分基本定理",
            "statement": "If F(x) = ∫[a,x] f(t)dt, then F'(x) = f(x)",
            "statement_cn": "如果 F(x) = ∫[a,x] f(t)dt，则 F'(x) = f(x)",
            "conditions": "f must be continuous on [a,b]",
            "applications": ["Integration", "Differentiation", "Area calculation"]
        },
        # More theorems can be added here
    },
    
    "proof_techniques": {
        "direct": {
            "name": "Direct Proof",
            "name_cn": "直接证明",
            "description": "Start from premises, derive conclusion step by step",
            "description_cn": "从前提开始，逐步推导出结论",
            "steps": ["State premises", "Apply logical rules", "Reach conclusion"]
        },
        "contradiction": {
            "name": "Proof by Contradiction",
            "name_cn": "反证法",
            "description": "Assume negation of conclusion, derive contradiction",
            "description_cn": "假设结论的否定，推导出矛盾",
            "steps": ["Assume ¬P", "Derive contradiction", "Conclude P"]
        },
        "induction": {
            "name": "Mathematical Induction",
            "name_cn": "数学归纳法",
            "description": "Prove base case, then inductive step",
            "description_cn": "证明基础情形，然后归纳步骤",
            "steps": ["Base case", "Inductive hypothesis", "Inductive step", "Conclusion"]
        }
    },
    
    "common_mistakes": {
        "division_zero": {
            "name": "Division by Zero",
            "name_cn": "除零错误",
            "description": "Never divide by zero or assume it's valid",
            "description_cn": "绝不能除以零或认为这是有效的"
        },
        "cancellation": {
            "name": "Improper Cancellation",
            "name_cn": "不当约分",
            "description": "Don't cancel terms without verifying non-zero",
            "description_cn": "不要在未验证非零的情况下约去项"
        },
        "domain": {
            "name": "Domain Violation",
            "name_cn": "定义域违反",
            "description": "Always check domain restrictions",
            "description_cn": "始终检查定义域限制"
        }
    }
}

def get_math_prompt(template_name: str, language: str = "zh", **kwargs) -> str:
    """Get a mathematical reasoning prompt template."""
    if template_name not in MATH_REASONING_PROMPTS:
        raise ValueError(f"Unknown template: {template_name}")
    
    if language not in ["zh", "en"]:
        language = "zh"  # Default fallback
    
    template = MATH_REASONING_PROMPTS[template_name][language]
    return template.format(**kwargs)

def get_math_context(context_type: str, language: str = "zh") -> dict:
    """Get mathematical context information."""
    if context_type not in MATH_KNOWLEDGE_BASE:
        return {}
    
    context = MATH_KNOWLEDGE_BASE[context_type]
    if language == "zh":
        # Convert to Chinese names where available
        if isinstance(context, dict):
            for key, value in context.items():
                if isinstance(value, dict) and f"name_{language}" in value:
                    value[f"name_localized"] = value.get(f"name_{language}")
    
    return context