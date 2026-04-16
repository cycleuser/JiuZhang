"""Linear Algebra course module - Vectors, Matrices, Eigenvalues."""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


VECTORS = KnowledgePoint(
    id="linear_algebra.vectors",
    name="Vectors",
    name_cn="向量",
    category="linear_algebra",
    level="high_school",
    description="Quantities with both magnitude and direction, represented as ordered lists of numbers",
    description_cn="既有大小又有方向的量，用有序数组表示。向量是线性代数的基本对象。",
    prerequisites=["geometry.coordinate"],
    related_points=["linear_algebra.matrices", "linear_algebra.dot_product"],
    code_examples=["linear_algebra/vectors.py"],
    visualization_types=["vector_arrow", "vector_addition", "vector_space"],
)

MATRICES = KnowledgePoint(
    id="linear_algebra.matrices",
    name="Matrices",
    name_cn="矩阵",
    category="linear_algebra",
    level="high_school",
    description="Rectangular arrays of numbers, used to represent linear transformations and systems of equations",
    description_cn="按矩形排列的数字阵列，用于表示线性变换和方程组。",
    prerequisites=["linear_algebra.vectors"],
    related_points=["linear_algebra.determinant", "linear_algebra.inverse"],
    code_examples=["linear_algebra/matrices.py"],
    visualization_types=["matrix_grid", "matrix_multiplication", "transformation"],
)

DETERMINANT = KnowledgePoint(
    id="linear_algebra.determinant",
    name="Determinant",
    name_cn="行列式",
    category="linear_algebra",
    level="high_school",
    description="A scalar value computed from a square matrix, indicating if the matrix is invertible",
    description_cn="从方阵计算出的标量值，表示矩阵是否可逆。也表示线性变换的缩放因子。",
    prerequisites=["linear_algebra.matrices"],
    related_points=["linear_algebra.inverse", "linear_algebra.eigenvalues"],
    code_examples=["linear_algebra/determinant.py"],
    visualization_types=["area_scaling", "volume_scaling"],
)

EIGENVALUES = KnowledgePoint(
    id="linear_algebra.eigenvalues",
    name="Eigenvalues and Eigenvectors",
    name_cn="特征值与特征向量",
    category="linear_algebra",
    level="undergraduate",
    description="For matrix A, vector v is an eigenvector if Av = λv, where λ is the eigenvalue",
    description_cn="对于矩阵A，如果Av = λv，则v是特征向量，λ是特征值。特征向量在变换中只缩放不改变方向。",
    prerequisites=["linear_algebra.determinant", "linear_algebra.matrices"],
    related_points=["linear_algebra.diagonalization", "linear_algebra.applications"],
    code_examples=["linear_algebra/eigenvalues.py"],
    visualization_types=["eigenvector_plot", "transformation_visualization"],
)


def get_linear_algebra_knowledge_points() -> list:
    return [VECTORS, MATRICES, DETERMINANT, EIGENVALUES]


def get_linear_algebra_lesson() -> Lesson:
    return Lesson(
        id="linear_algebra.intro",
        title="Vectors and Matrices",
        title_cn="向量与矩阵",
        knowledge_points=["linear_algebra.vectors", "linear_algebra.matrices"],
        content_cn="""# 向量与矩阵

## 1. 向量

**定义：** 既有大小又有方向的量。

**表示：**
- 几何：带箭头的线段
- 代数：有序数组 (x, y) 或 (x, y, z)

**向量运算：**
- 加法：对应分量相加
- 数乘：每个分量乘以标量
- 点积：a·b = |a||b|cos(θ) = a₁b₁ + a₂b₂ + ...
- 叉积：a×b（三维），结果是垂直于a和b的向量

**例子：**
a = (1, 2), b = (3, 4)
a + b = (4, 6)
a·b = 1×3 + 2×4 = 11
|a| = √(1² + 2²) = √5

## 2. 矩阵

**定义：** 按矩形排列的数字阵列。

**表示：** m行n列的矩阵记作 m×n 矩阵

**矩阵运算：**
- 加法：对应元素相加（同型矩阵）
- 数乘：每个元素乘以标量
- 乘法：A(m×n) × B(n×p) = C(m×p)
- 转置：行列互换

**矩阵乘法：**
C[i,j] = Σ A[i,k] × B[k,j]

**特殊矩阵：**
- 单位矩阵 I：对角线为1，其余为0
- 零矩阵：所有元素为0
- 对角矩阵：只有对角线有非零元素
- 对称矩阵：A = Aᵀ

## 3. 行列式

**2×2 行列式：**
|a b|
|c d| = ad - bc

**3×3 行列式：**
|a b c|
|d e f| = a(ei-fh) - b(di-fg) + c(dh-eg)
|g h i|

**性质：**
- det(AB) = det(A) × det(B)
- det(Aᵀ) = det(A)
- det(A⁻¹) = 1/det(A)
- det(A) = 0 ⇔ A不可逆

## 4. 特征值与特征向量

**定义：** Av = λv
- v 是特征向量（非零）
- λ 是特征值

**求法：**
1. 解特征方程：det(A - λI) = 0
2. 对每个λ，解 (A - λI)v = 0

**意义：**
- 特征向量：在变换中只缩放不改变方向
- 特征值：缩放因子
""",
        code_snippets=[
            {
                "title": "Vector Operations",
                "title_cn": "向量运算",
                "code": """import numpy as np

# 向量
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

print(f"a = {a}")
print(f"b = {b}")
print(f"a + b = {a + b}")
print(f"a · b = {np.dot(a, b)}")
print(f"|a| = {np.linalg.norm(a):.2f}")
print(f"a × b = {np.cross(a, b)}")

# 夹角
cos_theta = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
theta = np.degrees(np.arccos(cos_theta))
print(f"夹角 = {theta:.1f}°")""",
            },
            {
                "title": "Matrix Operations",
                "title_cn": "矩阵运算",
                "code": """import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print(f"A = \\n{A}")
print(f"B = \\n{B}")
print(f"A + B = \\n{A + B}")
print(f"A × B = \\n{A @ B}")
print(f"Aᵀ = \\n{A.T}")
print(f"det(A) = {np.linalg.det(A):.2f}")
print(f"A⁻¹ = \\n{np.linalg.inv(A)}")

# 特征值与特征向量
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"\\n特征值: {eigenvalues}")
print(f"特征向量: \\n{eigenvectors}")""",
            },
            {
                "title": "Matrix Visualization",
                "title_cn": "矩阵可视化",
                "code": """import numpy as np
import matplotlib.pyplot as plt

# 矩阵热力图
A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(A, cmap='coolwarm', aspect='auto')

for i in range(3):
    for j in range(3):
        ax.text(j, i, f'{A[i,j]}', ha='center', va='center',
                color='white' if abs(A[i,j]) > 5 else 'black',
                fontsize=14, fontweight='bold')

ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels(['列1', '列2', '列3'])
ax.set_yticklabels(['行1', '行2', '行3'])
plt.colorbar(im)
ax.set_title('矩阵热力图')
plt.tight_layout()
plt.show()""",
            },
        ],
        estimated_minutes=100,
    )
