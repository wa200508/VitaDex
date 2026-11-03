"""Placeholder illustrations drawn only when layout changes."""

import math
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Triangle
from kivy.metrics import dp
from kivy.uix.widget import Widget
from .widgets import INK, GREEN


class CreatureArt(Widget):
    """Small original vector illustrations; no network or image dependencies."""

    def __init__(self, organism, style="emerald", **kwargs):
        super().__init__(**kwargs)
        self.organism, self.style = organism, style
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        cx, cy, unit = x + w * 0.5, y + h * 0.50, min(w, h) * 0.32
        colors = {
            "emerald": (0.82, 0.88, 0.74, 1),
            "blue": (0.76, 0.88, 0.89, 1),
            "gold": (0.96, 0.88, 0.66, 1),
        }
        with self.canvas:
            Color(*colors.get(self.style, colors["emerald"]))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
            Color(1, 1, 0.95, 0.38)
            Ellipse(pos=(cx - unit * 1.2, cy - unit * 1.1), size=(unit * 2.4, unit * 2.4))
            Color(0.3, 0.48, 0.33, 0.18)
            for i in range(7):
                px = x + w * ((i * 0.173 + 0.11) % 0.9)
                py = y + h * ((i * 0.29 + 0.16) % 0.85)
                Ellipse(pos=(px, py), size=(dp(4), dp(4)))
            if self.organism.type == "Mammal":
                is_cat = self.organism.scientific_name == "Felis catus"
                Color(*((0.74, 0.47, 0.23, 1) if not is_cat else (0.55, 0.57, 0.55, 1)))
                Ellipse(pos=(cx - unit * 0.65, cy - unit * 0.65), size=(unit * 1.3, unit * 1.4))
                if is_cat:
                    Triangle(
                        points=[
                            cx - unit * 0.6,
                            cy + unit * 0.2,
                            cx - unit * 0.6,
                            cy + unit,
                            cx - unit * 0.1,
                            cy + unit * 0.55,
                        ]
                    )
                    Triangle(
                        points=[
                            cx + unit * 0.6,
                            cy + unit * 0.2,
                            cx + unit * 0.6,
                            cy + unit,
                            cx + unit * 0.1,
                            cy + unit * 0.55,
                        ]
                    )
                    Color(0.91, 0.69, 0.62, 1)
                    Triangle(
                        points=[
                            cx - unit * 0.48,
                            cy + unit * 0.4,
                            cx - unit * 0.49,
                            cy + unit * 0.77,
                            cx - unit * 0.23,
                            cy + unit * 0.52,
                        ]
                    )
                    Triangle(
                        points=[
                            cx + unit * 0.48,
                            cy + unit * 0.4,
                            cx + unit * 0.49,
                            cy + unit * 0.77,
                            cx + unit * 0.23,
                            cy + unit * 0.52,
                        ]
                    )
                else:
                    Color(0.43, 0.28, 0.17, 1)
                    Ellipse(pos=(cx - unit * 0.9, cy - unit * 0.1), size=(unit * 0.48, unit * 1.0))
                    Ellipse(pos=(cx + unit * 0.42, cy - unit * 0.1), size=(unit * 0.48, unit * 1.0))
                Color(0.94, 0.86, 0.68, 1)
                Ellipse(pos=(cx - unit * 0.37, cy - unit * 0.5), size=(unit * 0.74, unit * 0.54))
                Color(*INK)
                for direction in (-1, 1):
                    Ellipse(
                        pos=(cx + direction * unit * 0.27 - unit * 0.065, cy + unit * 0.13),
                        size=(unit * 0.13, unit * 0.15),
                    )
                    if is_cat:
                        for offset in (-0.1, 0.06, 0.2):
                            Line(
                                points=[
                                    cx + direction * unit * 0.2,
                                    cy - unit * 0.24,
                                    cx + direction * unit * 0.85,
                                    cy + unit * (offset - 0.2),
                                ],
                                width=1,
                            )
                Triangle(
                    points=[
                        cx - unit * 0.12,
                        cy - unit * 0.12,
                        cx + unit * 0.12,
                        cy - unit * 0.12,
                        cx,
                        cy - unit * 0.27,
                    ]
                )
                Line(points=[cx, cy - unit * 0.27, cx, cy - unit * 0.39], width=1.4)
            elif self.organism.type == "Tree":
                Color(0.42, 0.29, 0.18, 1)
                RoundedRectangle(
                    pos=(cx - unit * 0.1, cy - unit * 1.05),
                    size=(unit * 0.2, unit * 1.3),
                    radius=[unit * 0.03],
                )
                for direction in (-1, 1):
                    Line(
                        points=[
                            cx,
                            cy - unit * 0.2,
                            cx + direction * unit * 0.55,
                            cy + unit * 0.45,
                        ],
                        width=dp(3),
                    )
                # Original stylized lobed leaves, not diagnostic botanical drawings.
                leaf = [
                    (0, 1),
                    (0.22, 0.45),
                    (0.65, 0.65),
                    (0.5, 0.12),
                    (0.9, 0.1),
                    (0.48, -0.3),
                    (0.1, -0.55),
                    (-0.1, -0.55),
                    (-0.48, -0.3),
                    (-0.9, 0.1),
                    (-0.5, 0.12),
                    (-0.65, 0.65),
                    (-0.22, 0.45),
                ]
                for dx, dy, scale, tone in [
                    (-0.55, 0.3, 0.65, (0.68, 0.35, 0.2, 1)),
                    (0.5, 0.35, 0.66, (0.77, 0.43, 0.23, 1)),
                    (0, 0.8, 0.7, (0.87, 0.53, 0.25, 1)),
                ]:
                    Color(*tone)
                    px, py, size = cx + unit * dx, cy + unit * dy, unit * scale
                    for i, point in enumerate(leaf):
                        nxt = leaf[(i + 1) % len(leaf)]
                        Triangle(
                            points=[
                                px,
                                py,
                                px + point[0] * size,
                                py + point[1] * size,
                                px + nxt[0] * size,
                                py + nxt[1] * size,
                            ]
                        )
                    Color(0.98, 0.77, 0.48, 1)
                    Line(points=[px, py - size * 0.4, px, py + size * 0.65], width=1)
            elif self.organism.type == "Grass":
                for i in range(11):
                    dx = (i - 5) * 0.15
                    top = 0.2 + ((i * 7) % 9) * 0.09
                    Color(0.22 + i * 0.012, 0.42 + i * 0.012, 0.24, 1)
                    Triangle(
                        points=[
                            cx + unit * dx,
                            cy - unit * 0.9,
                            cx + unit * (dx + 0.12),
                            cy - unit * 0.9,
                            cx + unit * (dx * 1.35),
                            cy + unit * top,
                        ]
                    )
                for direction in (-1, 1):
                    stem_x = cx + direction * unit * 0.35
                    Color(0.36, 0.54, 0.29, 1)
                    Line(points=[stem_x, cy - unit * 0.8, stem_x, cy + unit * 1.05], width=1.5)
                    for i in range(4):
                        height = cy + unit * (0.35 + i * 0.18)
                        reach = unit * (0.35 - i * 0.07)
                        for side in (-1, 1):
                            Line(
                                points=[
                                    stem_x,
                                    height,
                                    stem_x + side * reach,
                                    height + unit * 0.15,
                                ],
                                width=1,
                            )
                            Ellipse(
                                pos=(stem_x + side * reach, height + unit * 0.13),
                                size=(unit * 0.09, unit * 0.12),
                            )
            elif self.organism.type == "Bird":
                Color(0.28, 0.32, 0.32, 1)
                Triangle(
                    points=[
                        cx - unit * 0.6,
                        cy - unit * 0.25,
                        cx - unit * 1.15,
                        cy - unit * 0.55,
                        cx - unit * 0.95,
                        cy + unit * 0.1,
                    ]
                )
                Ellipse(pos=(cx - unit * 0.65, cy - unit * 0.6), size=(unit * 1.35, unit * 1.25))
                Color(0.72, 0.35, 0.2, 1)
                Ellipse(pos=(cx - unit * 0.05, cy - unit * 0.49), size=(unit * 0.8, unit * 0.95))
                Color(0.23, 0.27, 0.27, 1)
                Ellipse(pos=(cx + unit * 0.14, cy + unit * 0.23), size=(unit * 0.73, unit * 0.73))
                Color(0.36, 0.4, 0.39, 1)
                Ellipse(pos=(cx - unit * 0.52, cy - unit * 0.17), size=(unit * 0.72, unit * 0.51))
                Color(0.89, 0.66, 0.19, 1)
                Triangle(
                    points=[
                        cx + unit * 0.78,
                        cy + unit * 0.65,
                        cx + unit * 1.15,
                        cy + unit * 0.48,
                        cx + unit * 0.78,
                        cy + unit * 0.42,
                    ]
                )
                Color(*INK)
                Ellipse(pos=(cx + unit * 0.61, cy + unit * 0.66), size=(unit * 0.1, unit * 0.1))
                for dx in (-0.18, 0.28):
                    Line(
                        points=[
                            cx + unit * dx,
                            cy - unit * 0.5,
                            cx + unit * dx,
                            cy - unit * 0.95,
                            cx + unit * (dx + 0.25),
                            cy - unit * 0.95,
                        ],
                        width=1.5,
                    )
            elif self.organism.type == "Fish":
                Color(0.15, 0.42, 0.46, 1)
                Triangle(
                    points=[
                        cx - unit * 0.55,
                        cy,
                        cx - unit * 1.3,
                        cy + unit * 0.65,
                        cx - unit * 1.3,
                        cy - unit * 0.65,
                    ]
                )
                Color(0.28, 0.62, 0.63, 1)
                Ellipse(pos=(cx - unit * 0.8, cy - unit * 0.48), size=(unit * 1.8, unit * 0.96))
                Color(0.9, 0.76, 0.36, 1)
                Triangle(
                    points=[
                        cx - unit * 0.2,
                        cy - unit * 0.15,
                        cx + unit * 0.3,
                        cy - unit * 0.1,
                        cx,
                        cy - unit * 0.65,
                    ]
                )
                Color(*INK)
                Ellipse(pos=(cx + unit * 0.52, cy + unit * 0.05), size=(unit * 0.13, unit * 0.13))
                Color(1, 1, 1, 0.7)
                for i in range(3):
                    Line(
                        circle=(
                            cx + unit * (1.15 + i * 0.2),
                            cy + unit * (0.4 + i * 0.4),
                            unit * 0.1,
                        ),
                        width=1.2,
                    )
            elif self.organism.type == "Plant":
                Color(*GREEN)
                Line(points=[cx, cy - unit, cx, cy + unit * 0.35], width=dp(3))
                Ellipse(pos=(cx, cy - unit * 0.65), size=(unit * 0.7, unit * 0.3))
                Ellipse(pos=(cx - unit * 0.7, cy - unit * 0.3), size=(unit * 0.7, unit * 0.3))
                Color(0.91, 0.64, 0.21, 1)
                for i in range(8):
                    angle = i * math.pi / 4
                    Ellipse(
                        pos=(
                            cx + math.cos(angle) * unit * 0.45 - unit * 0.25,
                            cy + unit * 0.4 + math.sin(angle) * unit * 0.45 - unit * 0.25,
                        ),
                        size=(unit * 0.5, unit * 0.5),
                    )
                Color(0.37, 0.29, 0.16, 1)
                Ellipse(pos=(cx - unit * 0.3, cy + unit * 0.1), size=(unit * 0.6, unit * 0.6))
            else:
                Color(*GREEN)
                for direction in (-1, 1):
                    for offset in (-0.4, 0, 0.4):
                        Line(
                            points=[
                                cx + direction * unit * 0.3,
                                cy + offset * unit,
                                cx + direction * unit * 0.85,
                                cy + (offset - 0.2) * unit,
                            ],
                            width=dp(2),
                        )
                    Line(
                        points=[
                            cx + direction * unit * 0.18,
                            cy + unit * 0.6,
                            cx + direction * unit * 0.4,
                            cy + unit,
                        ],
                        width=dp(2),
                    )
                Ellipse(pos=(cx - unit * 0.28, cy + unit * 0.35), size=(unit * 0.56, unit * 0.55))
                Color(0.3, 0.53, 0.29, 1)
                Ellipse(pos=(cx - unit * 0.52, cy - unit * 0.65), size=(unit * 1.04, unit * 1.25))
                Color(0.72, 0.82, 0.35, 1)
                Line(points=[cx, cy - unit * 0.6, cx, cy + unit * 0.5], width=dp(2))
                for dx, dy in [(-0.25, 0.2), (0.25, -0.1), (-0.22, -0.35)]:
                    Ellipse(
                        pos=(cx + unit * dx - unit * 0.08, cy + unit * dy - unit * 0.08),
                        size=(unit * 0.16, unit * 0.16),
                    )
