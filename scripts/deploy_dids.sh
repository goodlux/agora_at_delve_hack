#!/bin/bash
# deploy-dids.sh
# Script to generate and deploy DIDs for AT Protocol agents

set -e  # Exit on any error

# Configuration variables - adjust these as needed
DOMAIN="cred.at"
AGENTS=("alice" "bob" "charlie" "delve")
REMOTE_USER="root"
REMOTE_HOST="cred"
WWW_PATH="/var/www/cred.at"
LOCAL_OUTPUT_DIR="./generated_dids"

# Function to display script usage
function show_usage {
  echo "Usage: $0 [--install-deps] [--setup-ssl]"
  echo "  --install-deps  Install dependencies on the remote server"
  echo "  --setup-ssl     Set up SSL certificates with Let's Encrypt"
  exit 1
}

# Parse command line arguments
INSTALL_DEPS=false
SETUP_SSL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-deps)
      INSTALL_DEPS=true
      shift
      ;;
    --setup-ssl)
      SETUP_SSL=true
      shift
      ;;
    --help)
      show_usage
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      ;;
  esac
done

# Create local output directory
mkdir -p "$LOCAL_OUTPUT_DIR"

echo "===== Generating DID documents for domain: $DOMAIN ====="
echo "Agents: ${AGENTS[*]}"

# Check if did_generator.py exists in the scripts directory
if [ ! -f "./scripts/did_generator.py" ]; then
  echo "Error: did_generator.py not found in ./scripts directory"
  echo "Make sure you're running this script from the project root directory"
  exit 1
fi

# Run the DID generator script to create DIDs and key pairs
python3 ./scripts/did_generator.py "$DOMAIN" --agents "${AGENTS[@]}" --output "$LOCAL_OUTPUT_DIR"

echo "===== DIDs and key pairs generated successfully ====="

# Check if any files were generated
if [ ! -d "$LOCAL_OUTPUT_DIR/${AGENTS[0]}/.well-known" ]; then
  echo "Error: DID documents were not generated properly"
  exit 1
fi

# Install dependencies on the remote server if requested
if [ "$INSTALL_DEPS" = true ]; then
  echo "===== Installing dependencies on the remote server ====="
  ssh "$REMOTE_USER@$REMOTE_HOST" "apt-get update && apt-get install -y nginx"
fi

# Create the .well-known directories on the remote server for each agent
echo "===== Creating .well-known directories on remote server ====="
for agent in "${AGENTS[@]}"; do
  echo "Creating directory for $agent.$DOMAIN..."
  ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $WWW_PATH/$agent.$DOMAIN/.well-known"
done

# Upload the DID documents to the remote server
echo "===== Uploading DID documents to remote server ====="
for agent in "${AGENTS[@]}"; do
  echo "Uploading DID document for $agent.$DOMAIN..."
  scp "$LOCAL_OUTPUT_DIR/$agent/.well-known/did.json" "$REMOTE_USER@$REMOTE_HOST:$WWW_PATH/$agent.$DOMAIN/.well-known/"
done

# Store key files securely (you may want to adjust this based on your security requirements)
echo "===== Backing up key files ====="
mkdir -p "$LOCAL_OUTPUT_DIR/keys_backup"
for agent in "${AGENTS[@]}"; do
  cp "$LOCAL_OUTPUT_DIR/${agent}_private_key.pem" "$LOCAL_OUTPUT_DIR/keys_backup/"
  cp "$LOCAL_OUTPUT_DIR/${agent}_config.json" "$LOCAL_OUTPUT_DIR/keys_backup/"
done
echo "Private keys and config files backed up to $LOCAL_OUTPUT_DIR/keys_backup/"
echo "IMPORTANT: Keep these files secure!"

# Set proper permissions on the remote server
echo "===== Setting permissions on remote server ====="
ssh "$REMOTE_USER@$REMOTE_HOST" "chmod -R 755 $WWW_PATH"

# Configure Nginx properly (assuming nginx is already installed)
echo "===== Configuring Nginx ====="
cat > nginx_config.tmp << EOF
server {
    listen 80;
    listen [::]:80;
    
    server_name $DOMAIN www.$DOMAIN;
    
    root $WWW_PATH/$DOMAIN;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}

EOF

# Add server blocks for each agent
for agent in "${AGENTS[@]}"; do
  cat >> nginx_config.tmp << EOF
server {
    listen 80;
    listen [::]:80;
    
    server_name $agent.$DOMAIN;
    
    root $WWW_PATH/$agent.$DOMAIN;
    index index.html;
    
    location /.well-known/ {
        try_files \$uri \$uri/ =404;
    }
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}

EOF
done

# Upload Nginx configuration to the server
scp nginx_config.tmp "$REMOTE_USER@$REMOTE_HOST:/etc/nginx/sites-available/cred.at"
rm nginx_config.tmp

# Enable the site and restart Nginx
ssh "$REMOTE_USER@$REMOTE_HOST" "ln -sf /etc/nginx/sites-available/cred.at /etc/nginx/sites-enabled/ && nginx -t && systemctl restart nginx"

# Set up SSL certificates with Let's Encrypt if requested
if [ "$SETUP_SSL" = true ]; then
  echo "===== Setting up SSL certificates with Let's Encrypt ====="
  
  # Construct domain list for certbot
  DOMAIN_LIST="-d $DOMAIN"
  for agent in "${AGENTS[@]}"; do
    DOMAIN_LIST="$DOMAIN_LIST -d $agent.$DOMAIN"
  done
  
  # Install certbot and obtain certificates
  ssh "$REMOTE_USER@$REMOTE_HOST" "apt-get update && apt-get install -y certbot python3-certbot-nginx && certbot --nginx $DOMAIN_LIST --non-interactive --agree-tos --email admin@$DOMAIN"
  
  echo "SSL certificates installed successfully!"
fi

# Test if the DID documents are accessible
echo "===== Testing DID document access ====="
for agent in "${AGENTS[@]}"; do
  echo "Testing $agent.$DOMAIN/.well-known/did.json..."
  curl -s -o /dev/null -w "%{http_code}" "http://$agent.$DOMAIN/.well-known/did.json"
  if [ $? -eq 0 ]; then
    echo " ✅ Success"
  else
    echo " ❌ Failed"
  fi
done

echo "===== Deployment Complete ====="
echo ""
echo "Next steps:"
echo "1. Store the private keys and config files securely"
echo "2. Test accessing the DIDs at https://<agent>.$DOMAIN/.well-known/did.json"
echo "3. Use the generated config files for your AT Protocol implementation"
echo ""
echo "IMPORTANT: The private keys in $LOCAL_OUTPUT_DIR/keys_backup/ are sensitive!"
echo "Make sure to secure them properly and consider removing them once you've stored them safely."