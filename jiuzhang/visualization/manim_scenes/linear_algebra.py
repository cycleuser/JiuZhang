"""Linear algebra manim scenes."""

try:
    from manim import (
        Scene, Axes, NumberPlane, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
        Arrow, Line, Polygon,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False


class VectorScene(Scene):
    """Visualize vectors and vector operations."""

    def __init__(self, v1=(2, 1), v2=(1, 3), title="Vectors", **kwargs):
        super().__init__(**kwargs)
        self.v1 = v1
        self.v2 = v2
        self.title = title

    def construct(self):
        font = get_manim_font()
        plane = NumberPlane(
            x_range=[-3, 4, 1],
            y_range=[-1, 4, 1],
            x_length=8,
            y_length=5,
        )
        self.play(Create(plane))

        v1_arrow = Arrow(
            start=plane.c2p(0, 0),
            end=plane.c2p(self.v1[0], self.v1[1]),
            color=BLUE,
            buff=0,
        )
        v1_label = MathTex(r"\vec{v}_1", font_size=28, color=BLUE).next_to(v1_arrow, RIGHT)
        self.play(Create(v1_arrow), Write(v1_label))

        v2_arrow = Arrow(
            start=plane.c2p(0, 0),
            end=plane.c2p(self.v2[0], self.v2[1]),
            color=RED,
            buff=0,
        )
        v2_label = MathTex(r"\vec{v}_2", font_size=28, color=RED).next_to(v2_arrow, UP)
        self.play(Create(v2_arrow), Write(v2_label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class MatrixTransformScene(Scene):
    """Visualize matrix transformations."""

    def __init__(self, matrix=None, title="Matrix Transformation", **kwargs):
        super().__init__(**kwargs)
        self.matrix = matrix or [[2, 0], [0, 2]]
        self.title = title

    def construct(self):
        font = get_manim_font()
        plane = NumberPlane(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=8,
            y_length=8,
        )
        self.play(Create(plane))

        matrix_tex = MathTex(
            r"A = \begin{pmatrix} "
            rf"{self.matrix[0][0]} & {self.matrix[0][1]} \\ "
            rf"{self.matrix[1][0]} & {self.matrix[1][1]} "
            r"\end{pmatrix}",
            font_size=36,
        ).to_edge(UP)
        self.play(Write(matrix_tex))

        basis_e1 = Arrow(
            start=plane.c2p(0, 0),
            end=plane.c2p(1, 0),
            color=BLUE,
            buff=0,
        )
        basis_e2 = Arrow(
            start=plane.c2p(0, 0),
            end=plane.c2p(0, 1),
            color=RED,
            buff=0,
        )
        self.play(Create(basis_e1), Create(basis_e2))

        title_text = Text(self.title, font=font, font_size=32).to_edge(DOWN)
        self.play(Write(title_text))
        self.wait(1)


class EigenvalueScene(Scene):
    """Visualize eigenvalues and eigenvectors."""

    def __init__(self, eigenvalues=None, title="Eigenvalues", **kwargs):
        super().__init__(**kwargs)
        self.eigenvalues = eigenvalues or [2, -1]
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=8,
            y_length=4,
        )
        self.play(Create(axes))

        for i, ev in enumerate(self.eigenvalues):
            color = BLUE if ev > 0 else RED
            arrow = Arrow(
                start=axes.c2p(0, 0),
                end=axes.c2p(ev, 0),
                color=color,
                buff=0,
            )
            label = MathTex(rf"\lambda_{i+1} = {ev}", font_size=28, color=color)
            label.next_to(arrow, UP if ev > 0 else DOWN)
            self.play(Create(arrow), Write(label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
