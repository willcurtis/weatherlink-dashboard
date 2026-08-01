"""Reusable modern dashboard widgets."""

from __future__ import annotations

import math
import tkinter as tk

import customtkinter as ctk


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, accent: str = "#38BDF8", **kwargs):
        super().__init__(master, corner_radius=16, fg_color="#172033", **kwargs)
        ctk.CTkLabel(
            self, text=title.upper(), text_color="#94A3B8", font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=18, pady=(15, 2))
        self.value = ctk.CTkLabel(self, text="--", font=("Arial", 28, "bold"), text_color=accent)
        self.value.pack(anchor="w", padx=18)
        self.detail = ctk.CTkLabel(
            self, text="Waiting for data", text_color="#94A3B8", font=("Arial", 11)
        )
        self.detail.pack(anchor="w", padx=18, pady=(0, 15))

    def set(self, value: str, detail: str = "") -> None:
        self.value.configure(text=value)
        self.detail.configure(text=detail)


class Gauge(ctk.CTkFrame):
    def __init__(
        self, master, title: str, minimum: float, maximum: float, unit: str, accent: str, **kwargs
    ):
        super().__init__(master, corner_radius=16, fg_color="#172033", **kwargs)
        self.minimum, self.maximum, self.unit, self.accent = minimum, maximum, unit, accent
        ctk.CTkLabel(
            self, text=title.upper(), text_color="#94A3B8", font=("Arial", 11, "bold")
        ).pack(pady=(13, 0))
        self.canvas = tk.Canvas(self, width=190, height=130, bg="#172033", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8)
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
        canvas.create_arc(*bbox, start=20, extent=140, style="arc", width=12, outline="#28364D")
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
                fill="#F8FAFC",
                width=3,
            )
            canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=self.accent, outline="")
        label = "--" if self.value is None else f"{self.value:.1f}"
        canvas.create_text(
            cx,
            height * 0.88,
            text=f"{label} {self.unit}",
            fill="#F8FAFC",
            font=("Arial", 17, "bold"),
        )


class Compass(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=16, fg_color="#172033", **kwargs)
        ctk.CTkLabel(
            self, text="WIND DIRECTION", text_color="#94A3B8", font=("Arial", 11, "bold")
        ).pack(pady=(13, 0))
        self.canvas = tk.Canvas(self, width=170, height=145, bg="#172033", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
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
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#334155", width=2)
        for text, x, y in (
            ("N", cx, cy - r - 10),
            ("E", cx + r + 10, cy),
            ("S", cx, cy + r + 10),
            ("W", cx - r - 10, cy),
        ):
            c.create_text(x, y, text=text, fill="#94A3B8", font=("Arial", 10, "bold"))
        if self.degrees is not None:
            a = math.radians(self.degrees - 90)
            tip = (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)
            left = (cx + math.cos(a + 2.55) * r * 0.25, cy + math.sin(a + 2.55) * r * 0.25)
            right = (cx + math.cos(a - 2.55) * r * 0.25, cy + math.sin(a - 2.55) * r * 0.25)
            c.create_polygon(tip, left, (cx, cy), right, fill="#38BDF8", outline="")
            c.create_text(
                cx, h - 10, text=f"{self.degrees:.0f}°", fill="#F8FAFC", font=("Arial", 12, "bold")
            )
