"""Reusable modern dashboard widgets."""

from __future__ import annotations

import math
import tkinter as tk
from typing import ClassVar

import customtkinter as ctk

from .theme import BACKGROUND, BORDER, CARD, CAUTION, CYAN, DANGER, MUTED, SUBTLE, TEAL, TEXT
from .weather_window import ACTIVITY_NAMES, ActivityAssessment, WindowStatus


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, accent: str = CYAN, **kwargs):
        super().__init__(
            master,
            corner_radius=18,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        ctk.CTkLabel(self, text=title.upper(), text_color=MUTED, font=("Arial", 11, "bold")).pack(
            anchor="w", padx=18, pady=(15, 2)
        )
        self.value = ctk.CTkLabel(self, text="--", font=("Arial", 29, "bold"), text_color=accent)
        self.value.pack(anchor="w", padx=18)
        self.detail = ctk.CTkLabel(
            self, text="Waiting for data", text_color=MUTED, font=("Arial", 11)
        )
        self.detail.pack(anchor="w", padx=18, pady=(0, 15))

    def set(self, value: str, detail: str = "") -> None:
        self.value.configure(text=value)
        self.detail.configure(text=detail)


class WeatherWindow(ctk.CTkFrame):
    """Compact, accessible traffic-light guidance for outdoor activities."""

    _STYLE: ClassVar[dict[WindowStatus, tuple[str, str, str]]] = {
        WindowStatus.GOOD: ("GOOD", TEAL, BACKGROUND),
        WindowStatus.CAUTION: ("CAUTION", CAUTION, BACKGROUND),
        WindowStatus.AVOID: ("AVOID", DANGER, BACKGROUND),
        WindowStatus.UNKNOWN: ("WAITING", SUBTLE, TEXT),
    }

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=18,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(7, 2))
        ctk.CTkLabel(
            header,
            text="WEATHER WINDOW",
            height=18,
            text_color=MUTED,
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="RIGHT NOW",
            height=18,
            text_color=SUBTLE,
            font=("Arial", 9, "bold"),
        ).pack(side="right")

        self.rows: dict[str, tuple[ctk.CTkLabel, ctk.CTkLabel]] = {}
        for index, activity in enumerate(ACTIVITY_NAMES, start=1):
            self.grid_rowconfigure(index, weight=1, uniform="activity")
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.grid(row=index, column=0, sticky="nsew", padx=12, pady=1)
            row.grid_columnconfigure(2, weight=1)
            ctk.CTkLabel(
                row,
                text=activity,
                width=100,
                height=18,
                anchor="w",
                text_color=TEXT,
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=0, sticky="w", padx=(4, 4))
            badge = ctk.CTkLabel(
                row,
                text="WAITING",
                width=62,
                height=18,
                corner_radius=6,
                fg_color=SUBTLE,
                text_color=TEXT,
                font=("Arial", 8, "bold"),
            )
            badge.grid(row=0, column=1, padx=(0, 8))
            reason = ctk.CTkLabel(
                row,
                text="Waiting for data",
                height=18,
                anchor="w",
                text_color=MUTED,
                font=("Arial", 9),
            )
            reason.grid(row=0, column=2, sticky="ew")
            self.rows[activity] = badge, reason

    def set(self, assessments: tuple[ActivityAssessment, ...]) -> None:
        for assessment in assessments:
            row = self.rows.get(assessment.activity)
            if row is None:
                continue
            badge, reason = row
            label, color, text_color = self._STYLE[assessment.status]
            badge.configure(text=label, fg_color=color, text_color=text_color)
            reason.configure(text=assessment.reason)


class Gauge(ctk.CTkFrame):
    def __init__(
        self, master, title: str, minimum: float, maximum: float, unit: str, accent: str, **kwargs
    ):
        super().__init__(
            master,
            corner_radius=18,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self.minimum, self.maximum, self.unit, self.accent = minimum, maximum, unit, accent
        ctk.CTkLabel(self, text=title.upper(), text_color=MUTED, font=("Arial", 11, "bold")).pack(
            pady=(13, 0)
        )
        self.canvas = tk.Canvas(self, width=190, height=130, bg=CARD, highlightthickness=0)
        # Native Tk canvases are rectangular and are not clipped to the
        # CustomTkinter frame radius. Keep them inset so the rounded border
        # remains visible on every edge.
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.value: float | None = None
        self.bind("<Configure>", lambda _e: self.draw())

    def set(self, value: float | None) -> None:
        self.value = value
        self.draw()

    def draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 190)
        height = max(canvas.winfo_height(), 130)
        cx, cy, radius = width / 2, height * 0.72, min(width * 0.38, height * 0.55)
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
        canvas.create_arc(*bbox, start=20, extent=140, style="arc", width=12, outline=BORDER)
        if self.value is not None:
            ratio = min(max((self.value - self.minimum) / (self.maximum - self.minimum), 0), 1)
            canvas.create_arc(
                *bbox, start=160, extent=-140 * ratio, style="arc", width=12, outline=self.accent
            )
            angle = math.radians(160 - 140 * ratio)
            length = radius * 0.72
            canvas.create_line(
                cx,
                cy,
                cx + math.cos(angle) * length,
                cy - math.sin(angle) * length,
                fill=TEXT,
                width=3,
            )
            canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=self.accent, outline="")
        label = "--" if self.value is None else f"{self.value:.1f}"
        canvas.create_text(
            cx,
            height * 0.88,
            text=f"{label} {self.unit}",
            fill=TEXT,
            font=("Arial", 17, "bold"),
        )


class Compass(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=18,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        ctk.CTkLabel(
            self, text="WIND DIRECTION", text_color=MUTED, font=("Arial", 11, "bold")
        ).pack(pady=(13, 0))
        self.canvas = tk.Canvas(self, width=170, height=145, bg=CARD, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.degrees: float | None = None
        self.bind("<Configure>", lambda _e: self.draw())

    def set(self, degrees: float | None) -> None:
        self.degrees = degrees
        self.draw()

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 170), max(c.winfo_height(), 145)
        cx, cy, r = w / 2, h / 2 + 3, min(w, h) * 0.34
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=BORDER, width=2)
        for text, x, y in (
            ("N", cx, cy - r - 10),
            ("E", cx + r + 10, cy),
            ("S", cx, cy + r + 10),
            ("W", cx - r - 10, cy),
        ):
            c.create_text(x, y, text=text, fill=MUTED, font=("Arial", 10, "bold"))
        if self.degrees is not None:
            a = math.radians(self.degrees - 90)
            tip = (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)
            left = (cx + math.cos(a + 2.55) * r * 0.25, cy + math.sin(a + 2.55) * r * 0.25)
            right = (cx + math.cos(a - 2.55) * r * 0.25, cy + math.sin(a - 2.55) * r * 0.25)
            c.create_polygon(tip, left, (cx, cy), right, fill=CYAN, outline="")
            c.create_text(
                cx, h - 10, text=f"{self.degrees:.0f}°", fill=TEXT, font=("Arial", 12, "bold")
            )
