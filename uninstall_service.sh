#!/bin/bash
#
# SOCKS5 Proxy Bot - Service Uninstaller for Ubuntu
# This script removes the bot service and all files
#
# Usage: sudo ./uninstall_service.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="socks5-bot"
SERVICE_USER="socks5bot"
INSTALL_DIR="/opt/socks5-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/var/log/${SERVICE_NAME}"

echo -e "${RED}========================================${NC}"
echo -e "${RED}  SOCKS5 Proxy Bot - Service Uninstaller${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (sudo ./uninstall_service.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}This will remove:${NC}"
echo "  - Systemd service (${SERVICE_NAME})"
echo "  - Installation directory (${INSTALL_DIR})"
echo "  - Log directory (${LOG_DIR})"
echo "  - Service user (${SERVICE_USER})"
echo ""
read -p "Are you sure you want to continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5]${NC} Stopping service..."
if systemctl is-active --quiet ${SERVICE_NAME}; then
    systemctl stop ${SERVICE_NAME}
    echo "  ✓ Service stopped"
else
    echo "  ✓ Service not running"
fi

echo -e "${YELLOW}[2/5]${NC} Disabling and removing service..."
if [ -f "${SERVICE_FILE}" ]; then
    systemctl disable ${SERVICE_NAME}
    rm -f ${SERVICE_FILE}
    systemctl daemon-reload
    echo "  ✓ Service removed"
else
    echo "  ✓ Service file not found"
fi

echo -e "${YELLOW}[3/5]${NC} Removing installation directory..."
if [ -d "${INSTALL_DIR}" ]; then
    rm -rf ${INSTALL_DIR}
    echo "  ✓ Directory removed: ${INSTALL_DIR}"
else
    echo "  ✓ Directory not found"
fi

echo -e "${YELLOW}[4/5]${NC} Removing log directory..."
if [ -d "${LOG_DIR}" ]; then
    rm -rf ${LOG_DIR}
    echo "  ✓ Directory removed: ${LOG_DIR}"
else
    echo "  ✓ Directory not found"
fi

echo -e "${YELLOW}[5/5]${NC} Removing service user..."
if id -u ${SERVICE_USER} > /dev/null 2>&1; then
    userdel ${SERVICE_USER}
    echo "  ✓ User removed: ${SERVICE_USER}"
else
    echo "  ✓ User not found"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Uninstallation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The bot service has been completely removed."
