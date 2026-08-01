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
INSTALL_HOME="$(getent passwd "${INSTALL_USER}" | cut -d: -f6)"
VENV_DIR="${PROJECT_DIR}/.venv"
ENV_FILE="${PROJECT_DIR}/.env"
SERVICE_NAME="weatherlink-dashboard.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

if [[ "${INSTALL_USER}" == "root" ]]; then
    printf 'Run this script as the desktop user, not as root. It will request sudo only when needed.\n' >&2
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
After=graphical.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${INSTALL_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=DISPLAY=:0
Environment=XAUTHORITY=${INSTALL_HOME}/.Xauthority
ExecStartPre=/bin/sh -c 'until [ -S /tmp/.X11-unix/X0 ]; do sleep 2; done'
ExecStart=${VENV_DIR}/bin/weatherlink-dashboard --kiosk
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target"

printf '%s\n' "${SERVICE_CONTENT}" | sudo tee "${SERVICE_PATH}" >/dev/null
sudo chmod 644 "${SERVICE_PATH}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"

printf '%s\n' \
    "Kiosk startup is enabled." \
    "After adding credentials to ${ENV_FILE}, start it with:" \
    "  sudo systemctl start ${SERVICE_NAME}" \
    "View logs with:" \
    "  journalctl -u ${SERVICE_NAME} -f"
