#!/usr/bin/env bash
set -euo pipefail

ENABLE_KIOSK=false

usage() {
    printf '%s\n' \
        "Usage: $0 [--enable-kiosk]" \
        "" \
        "Installs WeatherLink Dashboard into a local virtual environment." \
        "" \
        "  --enable-kiosk  Also install and enable a systemd startup service." \
        "  -h, --help      Show this help text."
}

while (($#)); do
    case "$1" in
        --enable-kiosk) ENABLE_KIOSK=true ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'This installer is intended for Raspberry Pi OS or another systemd Linux system.\n' >&2
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_USER="$(id -un)"
VENV_DIR="${PROJECT_DIR}/.venv"
ENV_FILE="${PROJECT_DIR}/.env"
SERVICE_NAME="weatherlink-dashboard.service"
USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"
SERVICE_PATH="${USER_SYSTEMD_DIR}/${SERVICE_NAME}"
AUTOSTART_DIR="${HOME}/.config/autostart"
AUTOSTART_PATH="${AUTOSTART_DIR}/weatherlink-dashboard.desktop"

if [[ "${INSTALL_USER}" == "root" ]]; then
    printf 'Run this script as the desktop user, not as root.\n' >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    printf 'python3 is required. Install it with: sudo apt install python3 python3-venv python3-tk\n' >&2
    exit 1
fi

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install "${PROJECT_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
    cp "${PROJECT_DIR}/.env.example" "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
    printf 'Created %s. Add your WeatherLink credentials before starting the dashboard.\n' "${ENV_FILE}"
fi

if [[ "${ENABLE_KIOSK}" != true ]]; then
    printf '%s\n' \
        "Installation complete. Kiosk startup was not enabled." \
        "Run manually with: ${VENV_DIR}/bin/weatherlink-dashboard"
    exit 0
fi

if ! command -v systemctl >/dev/null 2>&1; then
    printf 'systemd is required for --enable-kiosk, but systemctl was not found.\n' >&2
    exit 1
fi

SERVICE_CONTENT="[Unit]
Description=WeatherLink fullscreen dashboard
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/weatherlink-dashboard --kiosk
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical-session.target"

AUTOSTART_CONTENT="[Desktop Entry]
Type=Application
Name=WeatherLink Dashboard
Comment=Start the WeatherLink kiosk service after desktop login
Exec=systemctl --user start ${SERVICE_NAME}
X-GNOME-Autostart-enabled=true"

mkdir -p "${USER_SYSTEMD_DIR}" "${AUTOSTART_DIR}"
printf '%s\n' "${SERVICE_CONTENT}" > "${SERVICE_PATH}"
printf '%s\n' "${AUTOSTART_CONTENT}" > "${AUTOSTART_PATH}"
chmod 644 "${SERVICE_PATH}" "${AUTOSTART_PATH}"
systemctl --user daemon-reload
systemctl --user enable "${SERVICE_NAME}"

printf '%s\n' \
    "Kiosk startup is enabled." \
    "The user service will inherit Wayland or XWayland settings from the desktop session." \
    "After adding credentials to ${ENV_FILE}, start it with:" \
    "  systemctl --user start ${SERVICE_NAME}" \
    "View logs with:" \
    "  journalctl --user -u ${SERVICE_NAME} -f"
