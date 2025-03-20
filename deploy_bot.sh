#!/bin/bash
# Deploy Delve Bot to Digital Ocean server

# Configuration
SERVER_USER="root"  # or your server username
SERVER_IP=""        # your server IP
SERVER_DIR="/root/delve_bot"  # where to deploy on the server
REPO_DIR="$(pwd)"   # current directory

# Check for server IP
if [ -z "$SERVER_IP" ]; then
  echo "Please edit this script to include your server IP address."
  exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Deploying Delve Bot to Digital Ocean ===${NC}"

# Create directories
echo -e "${YELLOW}Creating directories on server...${NC}"
ssh $SERVER_USER@$SERVER_IP "mkdir -p $SERVER_DIR/agora_at/{core,adapters,services}"

# Copy files
echo -e "${YELLOW}Copying files to server...${NC}"
scp $REPO_DIR/delve_bot.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/
scp -r $REPO_DIR/agora_at/core/* $SERVER_USER@$SERVER_IP:$SERVER_DIR/agora_at/core/
scp -r $REPO_DIR/agora_at/adapters/* $SERVER_USER@$SERVER_IP:$SERVER_DIR/agora_at/adapters/
scp -r $REPO_DIR/agora_at/services/* $SERVER_USER@$SERVER_IP:$SERVER_DIR/agora_at/services/
scp $REPO_DIR/agora_at/__init__.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/agora_at/
scp $REPO_DIR/examples/use_did_with_adapter.py $SERVER_USER@$SERVER_IP:$SERVER_DIR/

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
SERVICE_FILE="$(cat << EOF
[Unit]
Description=Delve Bluesky Bot
After=network.target

[Service]
User=$SERVER_USER
WorkingDirectory=$SERVER_DIR
Environment="PYTHONPATH=$SERVER_DIR"
Environment="BLUESKY_APP_PASSWORD=YOUR_APP_PASSWORD_HERE"
ExecStart=/usr/bin/python3 $SERVER_DIR/delve_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
)"

echo "$SERVICE_FILE" | ssh $SERVER_USER@$SERVER_IP "cat > /tmp/delve-bot.service"
ssh $SERVER_USER@$SERVER_IP "sudo mv /tmp/delve-bot.service /etc/systemd/system/"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
ssh $SERVER_USER@$SERVER_IP "sudo apt-get update && sudo apt-get install -y python3-pip"
ssh $SERVER_USER@$SERVER_IP "pip3 install pydantic cryptography aiohttp requests"

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Create an app password on Bluesky for the Delve account"
echo -e "2. Edit the service file: ${GREEN}sudo nano /etc/systemd/system/delve-bot.service${NC}"
echo -e "3. Set the BLUESKY_APP_PASSWORD environment variable"
echo -e "4. Enable and start the service:"
echo -e "   ${GREEN}sudo systemctl daemon-reload${NC}"
echo -e "   ${GREEN}sudo systemctl enable delve-bot.service${NC}"
echo -e "   ${GREEN}sudo systemctl start delve-bot.service${NC}"
echo -e "5. Check the service status:"
echo -e "   ${GREEN}sudo systemctl status delve-bot.service${NC}"
echo -e "6. View logs:"
echo -e "   ${GREEN}sudo journalctl -u delve-bot.service -f${NC}"
