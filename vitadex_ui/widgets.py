"""Shared palette, wrapping labels, layouts, and controls."""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

PAPER = (0.96, 0.95, 0.91, 1)
WHITE = (1, 0.995, 0.97, 1)
INK = (0.12, 0.23, 0.19, 1)
MUTED = (0.38, 0.45, 0.39, 1)
GREEN = (0.16, 0.36, 0.27, 1)
PALE = (0.87, 0.91, 0.84, 1)
BORDER = (0.82, 0.85, 0.78, 1)
GOLD = (0.76, 0.51, 0.19, 1)


def provenance_status(organism):
    return {
        "fictional": "FICTIONAL / no factual sources",
        "unreviewed": "UNREVIEWED / facts not verified",
        "source_checked": "SOURCE CHECKED / human review pending",
        "reviewed": f"REVIEWED / {len(organism.sources)} references",
    }[organism.content_kind]


def claim_sources(organism, field):
    ids = [source["id"] for source in organism.sources if field in source["supports"]]
    return ("  [" + ", ".join(ids) + "]") if ids else ""


def label(text="", size=16, color=INK, bold=False, **kwargs):
    """A wrapping label whose height follows its content."""
    widget = Label(
        text=text,
        font_size=dp(size),
        color=color,
        bold=bold,
        halign="left",
        valign="middle",
        size_hint_y=None,
        **kwargs,
    )
    widget.bind(width=lambda item, width: setattr(item, "text_size", (max(1, width), None)))
    widget.bind(texture_size=lambda item, size: setattr(item, "height", size[1] + dp(6)))
    return widget


def column(spacing=12, padding=0, **kwargs):
    box = BoxLayout(
        orientation="vertical", spacing=dp(spacing), padding=dp(padding), size_hint_y=None, **kwargs
    )
    box.bind(minimum_height=box.setter("height"))
    return box


def surface(widget, color=WHITE, radius=20):
    with widget.canvas.before:
        Color(*color)
        background = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])

    def resize(*_):
        background.pos, background.size = widget.pos, widget.size

    widget.bind(pos=resize, size=resize)
    return widget


class Action(Button):
    def __init__(self, primary=False, **kwargs):
        super().__init__(
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=WHITE if primary else GREEN,
            font_size=dp(14),
            bold=True,
            disabled_color=MUTED,
            size_hint_y=None,
            height=dp(46),
            **kwargs,
        )
        self.primary = primary
        with self.canvas.before:
            self.fill = Color(*(GREEN if primary else PALE))
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw, disabled=self.redraw)

    def redraw(self, *_):
        self.shape.pos, self.shape.size = self.pos, self.size
        base = GREEN if self.primary else PALE
        self.fill.rgba = (*base[:3], 0.4 if self.disabled else (0.7 if self.state == "down" else 1))
        self.text_size = (max(1, self.width - dp(12)), None)
        self.halign = "center"
