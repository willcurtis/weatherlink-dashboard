#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/weatherlink-dashboard-build.XXXXXX")"
DIST_DIR="${PROJECT_DIR}/dist"
APP_BUILD_DIST="${BUILD_DIR}/dist"
APP_NAME="WeatherLink Dashboard"
BUNDLE_ID="com.thetechshed.weatherlink-dashboard"
VERSION="$(PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_BIN}" -c 'from weatherlink_dashboard import __version__; print(__version__)')"
ARCH="$(uname -m)"
ICON_SOURCE="${PROJECT_DIR}/src/weatherlink_dashboard/assets/tts-round-outline.png"
ICONSET="${BUILD_DIR}/WeatherLinkDashboard.iconset"
ICON_FILE="${BUILD_DIR}/WeatherLinkDashboard.icns"
APP_PATH="${APP_BUILD_DIST}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/WeatherLink-Dashboard-${VERSION}-macOS-${ARCH}.dmg"
STAGING_DIR="${BUILD_DIR}/dmg"

trap 'rm -rf "${BUILD_DIR}"' EXIT

if [[ "$(uname -s)" != "Darwin" ]]; then
    printf 'macOS is required to build the application bundle.\n' >&2
    exit 1
fi
if [[ ! -x "${PYTHON_BIN}" ]]; then
    printf 'Python environment not found at %s\n' "${PYTHON_BIN}" >&2
    exit 1
fi

rm -rf "${APP_PATH}" "${STAGING_DIR}" "${DIST_DIR}/${APP_NAME}.app"
mkdir -p "${ICONSET}" "${DIST_DIR}" "${APP_BUILD_DIST}"

make_icon() {
    local size="$1"
    local output="$2"
    sips -z "${size}" "${size}" "${ICON_SOURCE}" --out "${output}" >/dev/null
}

make_icon 16 "${ICONSET}/icon_16x16.png"
make_icon 32 "${ICONSET}/icon_16x16@2x.png"
make_icon 32 "${ICONSET}/icon_32x32.png"
make_icon 64 "${ICONSET}/icon_32x32@2x.png"
make_icon 128 "${ICONSET}/icon_128x128.png"
make_icon 256 "${ICONSET}/icon_128x128@2x.png"
make_icon 256 "${ICONSET}/icon_256x256.png"
make_icon 512 "${ICONSET}/icon_256x256@2x.png"
make_icon 512 "${ICONSET}/icon_512x512.png"
cp "${ICON_SOURCE}" "${ICONSET}/icon_512x512@2x.png"
iconutil -c icns "${ICONSET}" -o "${ICON_FILE}"

"${PYTHON_BIN}" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${APP_NAME}" \
    --icon "${ICON_FILE}" \
    --osx-bundle-identifier "${BUNDLE_ID}" \
    --paths "${PROJECT_DIR}/src" \
    --collect-all customtkinter \
    --add-data "${ICON_SOURCE}:weatherlink_dashboard/assets" \
    --distpath "${APP_BUILD_DIST}" \
    --workpath "${BUILD_DIR}/pyinstaller" \
    --specpath "${BUILD_DIR}" \
    "${PROJECT_DIR}/scripts/macos_entry.py"

set_plist_string() {
    local key="$1"
    local value="$2"
    local plist="${APP_PATH}/Contents/Info.plist"
    /usr/libexec/PlistBuddy -c "Set :${key} ${value}" "${plist}" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :${key} string ${value}" "${plist}"
}

set_plist_string "CFBundleShortVersionString" "${VERSION}"
set_plist_string "CFBundleVersion" "${VERSION}"
/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "${APP_PATH}/Contents/Info.plist" 2>/dev/null || true
xattr -cr "${APP_PATH}"

if [[ -n "${MACOS_SIGN_IDENTITY:-}" ]]; then
    codesign --force --deep --options runtime --timestamp \
        --entitlements "${PROJECT_DIR}/packaging/macos/entitlements.plist" \
        --sign "${MACOS_SIGN_IDENTITY}" "${APP_PATH}"
    codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
else
    codesign --force --deep --sign - "${APP_PATH}"
    printf 'Created an ad-hoc signed build. Configure MACOS_SIGN_IDENTITY for public distribution.\n'
fi
codesign --verify --deep --strict --verbose=2 "${APP_PATH}"

mkdir -p "${STAGING_DIR}"
ditto --norsrc --noextattr "${APP_PATH}" "${STAGING_DIR}/${APP_NAME}.app"
xattr -cr "${STAGING_DIR}/${APP_NAME}.app"
codesign --verify --deep --strict --verbose=2 "${STAGING_DIR}/${APP_NAME}.app"
ln -s /Applications "${STAGING_DIR}/Applications"
rm -f "${DMG_PATH}"
hdiutil create -volname "${APP_NAME}" -srcfolder "${STAGING_DIR}" \
    -ov -format UDZO "${DMG_PATH}"

if [[ -n "${MACOS_SIGN_IDENTITY:-}" ]]; then
    codesign --force --timestamp --sign "${MACOS_SIGN_IDENTITY}" "${DMG_PATH}"
fi

if [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "${APPLE_APP_PASSWORD:-}" ]]; then
    xcrun notarytool submit "${DMG_PATH}" \
        --apple-id "${APPLE_ID}" \
        --team-id "${APPLE_TEAM_ID}" \
        --password "${APPLE_APP_PASSWORD}" \
        --wait
    xcrun stapler staple "${APP_PATH}"
    xcrun stapler staple "${DMG_PATH}"
fi

printf 'Created %s\n' "${DMG_PATH}"
