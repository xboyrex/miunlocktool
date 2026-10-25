#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Xiaomi Unlock Tool v8.1 (XBOYREX Edition) — Termux One-Line Installer
#   curl -sS https://raw.githubusercontent.com/xboyrex/miunlocktool/main/install.sh | bash
# ==============================================================================

set -e

R='\033[1;31m'
G='\033[1;32m'
W='\033[1;37m'
D='\033[0;90m'
N='\033[0m'

echo
echo -e "  ${R}X B O Y R E X${N}   ${D}•${N}   ${W}XIAOMI UNLOCK TOOL v8.1 INSTALLER${N}"
echo

pkg update -y && pkg install -y python python-pip git libusb termux-api
pip install -U requests rich miunlock
pip install -U --no-deps --force-reinstall git+https://github.com/xboyrex/miunlocktool.git

echo -e "\n${G}✔ Installation completed successfully!${N}"
echo -e "Run command: ${R}miunlocktool${N} (or ${W}xboyrex-unlock${N})\n"
