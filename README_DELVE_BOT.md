# Delve Bot for Bluesky

This project implements a Bluesky bot for the Delve agent, connecting the Agora protocol with the AT Protocol ecosystem.

## Overview

The Delve bot authenticates with Bluesky using a decentralized identifier (DID) and monitors the platform for mentions. When mentioned, it generates responses and engages with users, serving as a bridge between different agent networks.

## Features

- Authenticates with Bluesky using DID-based cryptography
- Monitors for mentions and responds to users
- Posts status updates and information
- Runs continuously as a systemd service on a server

## Prerequisites

- Python 3.7+
- Required Python packages: pydantic, cryptography, aiohttp, requests
- A Bluesky account with an app password
- Deployed DIDs on a web server (see did_deployment_documentation.md)

## Setup and Deployment

### Local Development

1. Install dependencies:
   ```
   pip install pydantic cryptography aiohttp requests
   ```

2. Run the bot locally:
   ```
   export BLUESKY_APP_PASSWORD=your_app_password
   python delve_bot.py
   ```

### Server Deployment

1. Edit the `deploy_bot.sh` script with your server details:
   - Set SERVER_USER to your server username
   - Set SERVER_IP to your server's IP address

2. Make the script executable and run it:
   ```
   chmod +x deploy_bot.sh
   ./deploy_bot.sh
   ```

3. Follow the on-screen instructions to complete deployment

## Configuration

The bot can be configured via environment variables or a JSON configuration file:

- `BLUESKY_APP_PASSWORD`: App password for Bluesky authentication
- `ATPROTO_KEY_PATH`: Path to the directory containing DID private keys (default: ~/secure_location/agora_at_keys)

## Architecture

The bot is built using several key components:

1. **Agent Model**: Represents the Delve agent's identity and capabilities
2. **ATProtoAdapter**: Handles communication with the AT Protocol (Bluesky)
3. **DelveBot**: Main bot logic including mention monitoring and response generation

## Next Steps

- Enhance the response generation with AI/LLM integration
- Add more sophisticated interaction patterns
- Connect with other specialized agents for distributed tasks
- Implement caching and knowledge persistence using AT Protocol

## License

[Your license information here]

## Contact

[Your contact information here]
