#!/bin/bash
#
# SOCKS5 Proxy Bot - Systemd Service Installer for Ubuntu
# This script installs the bot as a system service
#
# Usage: sudo ./install_service.sh
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
VENV_DIR="${INSTALL_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/var/log/${SERVICE_NAME}"
ENV_FILE="${INSTALL_DIR}/.env"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SOCKS5 Proxy Bot - Service Installer${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (sudo ./install_service.sh)${NC}"
    exit 1
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is not installed${NC}"
    echo "Install with: apt update && apt install -y python3 python3-pip python3-venv"
    exit 1
fi

echo -e "${YELLOW}[1/8]${NC} Creating service user..."
if ! id -u ${SERVICE_USER} > /dev/null 2>&1; then
    useradd --system --no-create-home --shell /bin/false ${SERVICE_USER}
    echo "  ✓ User ${SERVICE_USER} created"
else
    echo "  ✓ User ${SERVICE_USER} already exists"
fi

echo -e "${YELLOW}[2/8]${NC} Creating installation directory..."
mkdir -p ${INSTALL_DIR}
mkdir -p ${LOG_DIR}
chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
chown -R ${SERVICE_USER}:${SERVICE_USER} ${LOG_DIR}
echo "  ✓ Directories created: ${INSTALL_DIR}, ${LOG_DIR}"

echo -e "${YELLOW}[3/8]${NC} Copying bot files..."
# Copy all files from current directory to install directory
cp -r ./* ${INSTALL_DIR}/
chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
echo "  ✓ Files copied to ${INSTALL_DIR}"

echo -e "${YELLOW}[4/8]${NC} Setting up Python virtual environment..."
cd ${INSTALL_DIR}
python3 -m venv ${VENV_DIR}
echo "  ✓ Virtual environment created at ${VENV_DIR}"

echo -e "${YELLOW}[5/8]${NC} Installing Python dependencies..."
${VENV_DIR}/bin/pip install --upgrade pip
${VENV_DIR}/bin/pip install -r ${INSTALL_DIR}/requirements.txt
echo "  ✓ Dependencies installed"

echo -e "${YELLOW}[6/8]${NC} Creating environment file..."
if [ ! -f "${ENV_FILE}" ]; then
    cp ${INSTALL_DIR}/.env.example ${ENV_FILE}
    echo ""
    echo -e "${YELLOW}  ⚠️  IMPORTANT: Edit ${ENV_FILE} and add your Telegram bot token!${NC}"
    echo "  Use: nano ${ENV_FILE}"
    echo ""
    read -p "  Press Enter after you've added the token, or 's' to skip and edit later: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "  ⚠️  Remember to edit .env before starting the service!"
    fi
else
    echo "  ✓ Environment file already exists"
fi
chown ${SERVICE_USER}:${SERVICE_USER} ${ENV_FILE}

echo -e "${YELLOW}[7/8]${NC} Creating systemd service..."
cat > ${SERVICE_FILE} << EOF
[Unit]
Description=SOCKS5 Proxy Telegram Bot
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/python ${INSTALL_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=append:${LOG_DIR}/bot.log
StandardError=append:${LOG_DIR}/bot.error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
echo "  ✓ Service file created at ${SERVICE_FILE}"

echo -e "${YELLOW}[8/8]${NC} Enabling and starting service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}
echo "  ✓ Service enabled and started"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Service Name:  ${GREEN}${SERVICE_NAME}${NC}"
echo -e "Install Dir:   ${GREEN}${INSTALL_DIR}${NC}"
echo -e "Log File:      ${GREEN}${LOG_DIR}/bot.log${NC}"
echo -e "Error Log:     ${GREEN}${LOG_DIR}/bot.error.log${NC}"
echo -e "Env File:      ${GREEN}${ENV_FILE}${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  Check status:     ${GREEN}systemctl status ${SERVICE_NAME}${NC}"
echo "  View logs:        ${GREEN}journalctl -u ${SERVICE_NAME} -f${NC}"
echo "  Stop service:     ${GREEN}systemctl stop ${SERVICE_NAME}${NC}"
echo "  Start service:    ${GREEN}systemctl start ${SERVICE_NAME}${NC}"
echo "  Restart service:  ${GREEN}systemctl restart ${SERVICE_NAME}${NC}"
echo "  Disable service:  ${GREEN}systemctl disable ${SERVICE_NAME}${NC}"
echo ""
echo -e "${YELLOW}To update the bot:${NC}"
echo "  1. Copy new files to ${INSTALL_DIR}"
echo "  2. Run: ${GREEN}systemctl restart ${SERVICE_NAME}${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC} Make sure you've added your bot token to ${ENV_FILE}"
echo "  Edit with: ${GREEN}nano ${ENV_FILE}${NC}"
echo "  Then restart: ${GREEN}systemctl restart ${SERVICE_NAME}${NC}"
echo ""
