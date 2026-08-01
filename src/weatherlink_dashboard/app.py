"""CustomTkinter desktop application."""

from __future__ import annotations

import argparse
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib.resources import files

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure
from PIL import Image, ImageTk

from . import __version__
from .client import WeatherLinkClient, WeatherLinkError
from .config import ConfigurationError, Settings, save_user_config, user_config_path
from .models import Conditions, history_series, parse_current
from .theme import (
    BACKGROUND,
    BORDER,
    CARD,
    CYAN,
    CYAN_HOVER,
    DANGER,
    GRID,
    MUTED,
    SUBTLE,
    SURFACE,
    TEAL,
    TEAL_HOVER,
    TEXT,
)
from .widgets import Compass, Gauge, MetricCard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

REPOSITORY_URL = "https://github.com/willcurtis/weatherlink-dashboard"


def display(value: float | None, suffix: str, decimals: int = 1) -> str:
    return "--" if value is None else f"{value:.{decimals}f} {suffix}"


def open_repository() -> bool:
    return webbrowser.open(REPOSITORY_URL)


class SetupDialog(ctk.CTk):
    """First-launch configuration for Finder-installed application bundles."""

    def __init__(self, error: str):
        super().__init__()
        self.saved = False
        self.title("Set up WeatherLink Dashboard")
        self.geometry("560x500")
        self.resizable(False, False)
        self.configure(fg_color=BACKGROUND)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(100, self._present)

        panel = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER
        )
        panel.pack(fill="both", expand=True, padx=24, pady=24)
        ctk.CTkLabel(
            panel, text="Connect your weather station", font=("Arial", 24, "bold"), text_color=TEXT
        ).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            panel,
            text="Enter your WeatherLink v2 credentials. They are saved in your user application-data folder, never inside the app.",
            wraplength=460,
            justify="left",
            text_color=MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 14))

        self.api_key = self._field(panel, "API key")
        self.api_secret = self._field(panel, "API secret", show="•")
        self.station_id = self._field(panel, "Station ID (optional)")
        self.error_label = ctk.CTkLabel(
            panel, text=error, wraplength=460, justify="left", text_color=DANGER
        )
        self.error_label.pack(anchor="w", padx=24, pady=(12, 4))
        ctk.CTkButton(
            panel,
            text="Save and open dashboard",
            height=40,
            fg_color=CYAN,
            hover_color=CYAN_HOVER,
            text_color=BACKGROUND,
            font=("Arial", 12, "bold"),
            command=self._save,
        ).pack(fill="x", padx=24, pady=(8, 24))

    def _present(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _field(self, master, label: str, show: str | None = None) -> ctk.CTkEntry:
        ctk.CTkLabel(master, text=label, text_color=MUTED, font=("Arial", 11, "bold")).pack(
            anchor="w", padx=24, pady=(8, 3)
        )
        entry = ctk.CTkEntry(
            master,
            height=38,
            show=show or "",
            fg_color=CARD,
            border_color=BORDER,
            text_color=TEXT,
        )
        entry.pack(fill="x", padx=24)
        return entry

    def _save(self) -> None:
        key = self.api_key.get().strip()
        secret = self.api_secret.get().strip()
        if not key or not secret:
            self.error_label.configure(text="API key and API secret are required.")
            return
        try:
            save_user_config(key, secret, self.station_id.get())
        except (OSError, ValueError) as exc:
            self.error_label.configure(text=f"Could not save configuration: {exc}")
            return
        self.saved = True
        self.quit()
        self.destroy()

    def _close(self) -> None:
        self.quit()
        self.destroy()


class Dashboard(ctk.CTk):
    def __init__(self, settings: Settings, kiosk: bool = False):
        super().__init__()
        self.settings = settings
        self.metric = settings.units == "metric"
        self.client = WeatherLinkClient(settings.api_key, settings.api_secret)
        self.station_id = settings.station_id
        self.station_name = "Weather station"
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loading = False
        self.refresh_after_id: str | None = None
        self.title("The Tech Shed | WeatherLink Dashboard")
        self.geometry("1220x820")
        self.minsize(980, 700)
        self.configure(fg_color=BACKGROUND)
        logo_path = files("weatherlink_dashboard").joinpath("assets/tts-round-outline.png")
        logo_image = Image.open(logo_path)
        self.logo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(76, 76))
        self.window_icon = ImageTk.PhotoImage(logo_image.resize((64, 64)))
        self.iconphoto(True, self.window_icon)
        self.protocol("WM_DELETE_WINDOW", self.close)
        if kiosk:
            self.attributes("-fullscreen", True)
            self.bind("<F11>", self._toggle_fullscreen)
            self.bind("<Escape>", self._leave_fullscreen)
        self._build()
        self._schedule_refresh(200)

    def _toggle_fullscreen(self, _event=None) -> None:
        self.attributes("-fullscreen", not bool(self.attributes("-fullscreen")))

    def _leave_fullscreen(self, _event=None) -> None:
        self.attributes("-fullscreen", False)

    def _cancel_scheduled_refresh(self) -> None:
        if self.refresh_after_id is None:
            return
        self.after_cancel(self.refresh_after_id)
        self.refresh_after_id = None

    def _schedule_refresh(self, delay_ms: int) -> None:
        self._cancel_scheduled_refresh()
        self.refresh_after_id = self.after(delay_ms, self._run_scheduled_refresh)

    def _run_scheduled_refresh(self) -> None:
        self.refresh_after_id = None
        self.refresh()

    def _build(self) -> None:
        ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=TEAL).pack(fill="x")
        header = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER
        )
        header.pack(fill="x", padx=30, pady=(18, 12))
        ctk.CTkLabel(header, text="", image=self.logo).pack(side="left", padx=(18, 14), pady=10)
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", pady=12)
        ctk.CTkLabel(
            title_box,
            text="THE TECH SHED  /  WEATHER INTELLIGENCE",
            font=("Arial", 10, "bold"),
            text_color=TEAL,
        ).pack(anchor="w")
        self.title_label = ctk.CTkLabel(
            title_box, text=self.station_name, font=("Arial", 27, "bold"), text_color=TEXT
        )
        self.title_label.pack(anchor="w")
        self.status = ctk.CTkLabel(title_box, text="Connecting…", text_color=MUTED)
        self.status.pack(anchor="w")
        self.refresh_button = ctk.CTkButton(
            header,
            text="Refresh data",
            width=126,
            height=38,
            corner_radius=12,
            fg_color=CYAN,
            hover_color=CYAN_HOVER,
            text_color=BACKGROUND,
            font=("Arial", 12, "bold"),
            command=self.refresh,
        )
        self.refresh_button.pack(side="right", padx=20)

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.pack(fill="x", padx=24, pady=4)
        for index in range(4):
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
        self.temp_card = MetricCard(metrics, "Outside temperature", CYAN)
        self.hum_card = MetricCard(metrics, "Humidity", TEAL)
        self.rain_card = MetricCard(metrics, "Rain today", CYAN)
        self.solar_card = MetricCard(metrics, "Solar / UV", TEAL)
        for i, card in enumerate((self.temp_card, self.hum_card, self.rain_card, self.solar_card)):
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")

        visuals = ctk.CTkFrame(self, fg_color="transparent")
        visuals.pack(fill="x", padx=24, pady=4)
        for index in range(3):
            visuals.grid_columnconfigure(index, weight=1, uniform="visual")
        wind_unit = "km/h" if self.metric else "mph"
        pressure_unit = "hPa" if self.metric else "inHg"
        self.wind_gauge = Gauge(
            visuals, "Wind speed", 0, 100 if self.metric else 60, wind_unit, CYAN
        )
        self.pressure_gauge = Gauge(
            visuals,
            "Pressure",
            950 if self.metric else 28,
            1050 if self.metric else 31,
            pressure_unit,
            TEAL,
        )
        self.compass = Compass(visuals)
        for i, widget in enumerate((self.wind_gauge, self.pressure_gauge, self.compass)):
            widget.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")

        chart_frame = ctk.CTkFrame(
            self, corner_radius=18, fg_color=CARD, border_width=1, border_color=BORDER
        )
        chart_header = ctk.CTkFrame(chart_frame, fg_color="transparent")
        chart_header.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(
            chart_header, text="24-HOUR HISTORY", text_color=MUTED, font=("Arial", 11, "bold")
        ).pack(side="left")
        self.chart_choice = ctk.CTkSegmentedButton(
            chart_header,
            values=["Temperature", "Humidity", "Pressure", "Wind"],
            selected_color=TEAL,
            selected_hover_color=TEAL_HOVER,
            unselected_color=SURFACE,
            unselected_hover_color=BORDER,
            text_color=TEXT,
            command=lambda _: self._draw_chart(),
        )
        self.chart_choice.set("Temperature")
        self.chart_choice.pack(side="right")
        self.figure = Figure(figsize=(8, 3), dpi=100, facecolor=CARD)
        self.axes = self.figure.add_subplot(111)
        self.chart = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.chart.get_tk_widget().configure(bg=CARD, highlightthickness=0)
        self.chart.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=8)
        self.series: dict[str, list[tuple[int, float]]] = {}
        self._draw_chart()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        # Reserve the footer before allowing the history chart to consume
        # the remaining space. This keeps it visible on the first layout pass.
        footer.pack(side="bottom", fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(
            footer,
            text=f"WeatherLink Dashboard v{__version__}",
            text_color=SUBTLE,
            font=("Arial", 10),
        ).pack(side="left")
        copyright_label = ctk.CTkLabel(
            footer,
            text="© 2026 The Tech Shed",
            text_color=CYAN,
            font=("Arial", 10, "underline"),
            cursor="hand2",
        )
        copyright_label.pack(side="right")
        copyright_label.bind("<Button-1>", lambda _event: open_repository())
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(10, 12))

    def refresh(self) -> None:
        if self.loading:
            return
        self._cancel_scheduled_refresh()
        self.loading = True
        self.refresh_button.configure(state="disabled")
        self.status.configure(text="Refreshing WeatherLink data…", text_color=MUTED)
        future = self.executor.submit(self._fetch)
        future.add_done_callback(lambda f: self.after(0, self._finish_refresh, f))

    def _fetch(self):
        if not self.station_id:
            stations = self.client.stations()
            if not stations:
                raise WeatherLinkError("No stations are available to this WeatherLink account")
            station = stations[0]
            self.station_id = str(station.get("station_id") or station.get("station_id_uuid"))
            self.station_name = station.get("station_name", "Weather station")
        current = self.client.current(self.station_id)
        try:
            historic = self.client.historic(self.station_id, self.settings.history_hours)
        except WeatherLinkError:
            historic = {"sensors": []}  # Basic plans may not include history.
        return parse_current(current), history_series(historic, self.metric)

    def _finish_refresh(self, future) -> None:
        self.loading = False
        self.refresh_button.configure(state="normal")
        try:
            conditions, self.series = future.result()
        except (WeatherLinkError, ValueError, KeyError, TypeError) as exc:
            self.status.configure(text=str(exc), text_color=DANGER)
        else:
            self._show_conditions(conditions)
            self._draw_chart()
        self._schedule_refresh(self.settings.refresh_seconds * 1000)

    def _show_conditions(self, c: Conditions) -> None:
        temp_unit = "°C" if self.metric else "°F"
        rain_unit = "mm" if self.metric else "in"
        self.title_label.configure(text=self.station_name)
        self.status.configure(text=f"LIVE  •  Observed {c.observed_at}", text_color=TEAL)
        self.temp_card.set(
            display(c.temperature(self.metric), temp_unit),
            f"Feels like {display(c.feels_like(self.metric), temp_unit)}",
        )
        self.hum_card.set(display(c.humidity, "%", 0), "Relative humidity")
        self.rain_card.set(
            display(c.rain_day(self.metric), rain_unit),
            f"Rate {display(c.rain_rate(self.metric), rain_unit + '/h')}",
        )
        solar = display(c.solar_wm2, "W/m²", 0)
        self.solar_card.set(solar, f"UV index {display(c.uv_index, '', 1)}")
        self.wind_gauge.set(c.wind(self.metric))
        self.pressure_gauge.set(c.pressure(self.metric))
        self.compass.set(c.wind_direction)

    def _draw_chart(self) -> None:
        choice = getattr(self, "chart_choice", None)
        key = choice.get().lower() if choice else "temperature"
        points = self.series.get(key, [])
        units = {
            "temperature": "°C" if self.metric else "°F",
            "humidity": "%",
            "pressure": "hPa" if self.metric else "inHg",
            "wind": "km/h" if self.metric else "mph",
        }
        ax = self.axes
        ax.clear()
        ax.set_facecolor(CARD)
        ax.tick_params(colors=MUTED, labelsize=8)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.75)
        ax.set_ylabel(units[key], color=MUTED, fontsize=9)
        if points:
            dates = [datetime.fromtimestamp(ts, tz=timezone.utc).astimezone() for ts, _ in points]
            values = [value for _, value in points]
            ax.plot(dates, values, color=CYAN, linewidth=2.3)
            ax.fill_between(dates, values, min(values), color=TEAL, alpha=0.10)
            ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        else:
            ax.text(
                0.5,
                0.5,
                "Historical data is unavailable for this station or plan",
                ha="center",
                va="center",
                color=SUBTLE,
                transform=ax.transAxes,
            )
        self.figure.tight_layout(pad=1.2)
        self.chart.draw_idle()

    def close(self) -> None:
        self._cancel_scheduled_refresh()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Davis WeatherLink desktop dashboard")
    parser.add_argument(
        "--kiosk",
        action="store_true",
        help="start fullscreen (press Escape to leave fullscreen and F11 to toggle it)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        settings = Settings.load()
    except ConfigurationError as exc:
        dialog = SetupDialog(
            f"{exc}\nConfiguration file: {user_config_path()}",
        )
        dialog.mainloop()
        if not dialog.saved:
            sys.exit(2)
        settings = Settings.load(user_config_path())
    Dashboard(settings, kiosk=args.kiosk).mainloop()


if __name__ == "__main__":
    main()
