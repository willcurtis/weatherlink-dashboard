from weatherlink_dashboard.app import build_parser


def test_kiosk_is_opt_in():
    assert build_parser().parse_args([]).kiosk is False
    assert build_parser().parse_args(["--kiosk"]).kiosk is True
