from weatherlink_dashboard.app import REPOSITORY_URL, Dashboard, build_parser, open_repository


def test_kiosk_is_opt_in():
    assert build_parser().parse_args([]).kiosk is False
    assert build_parser().parse_args(["--kiosk"]).kiosk is True


def test_refresh_schedule_replaces_existing_timer():
    dashboard = object.__new__(Dashboard)
    dashboard.refresh_after_id = "old-timer"
    cancelled = []
    scheduled = []
    dashboard.after_cancel = cancelled.append
    dashboard.after = lambda delay, callback: scheduled.append((delay, callback)) or "new-timer"

    dashboard._schedule_refresh(30_000)

    assert cancelled == ["old-timer"]
    assert scheduled == [(30_000, dashboard._run_scheduled_refresh)]
    assert dashboard.refresh_after_id == "new-timer"


def test_running_timer_clears_id_before_refresh():
    dashboard = object.__new__(Dashboard)
    dashboard.refresh_after_id = "active-timer"
    states = []
    dashboard.refresh = lambda: states.append(dashboard.refresh_after_id)

    dashboard._run_scheduled_refresh()

    assert states == [None]


def test_repository_link_opens_project_page(monkeypatch):
    opened = []
    monkeypatch.setattr(
        "weatherlink_dashboard.app.webbrowser.open", lambda url: opened.append(url) or True
    )

    assert open_repository() is True
    assert opened == [REPOSITORY_URL]
