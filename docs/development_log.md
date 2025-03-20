# DEVELOPMENT LOG: AGORA-AT INTEGRATION

## 2025-03-15 8:35PM PST - Domain Configuration and AT Protocol Identity Setup

### OBJECTIVE
Configure domain and establish AT Protocol identities for our agent network.

### DOMAIN CONFIGURATION STEPS

1. **Select Base Domain**
   - Choose an existing domain you control for the agent subdomains
   - Ensure you have DNS management access

2. **Subdomain Configuration**
   - Create DNS A or CNAME records for:
     - `alice.yourdomain.com` → Points to your development server
     - `delve.yourdomain.com` → Points to the cloud agent server
   - Ensure DNS propagation (can take up to 24 hours)

3. **Well-Known DID Configuration**
   - For each subdomain, create a `.well-known` directory
   - Add a `did.json` file at `.well-known/did.json` with the following structure:

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1"
  ],
  "id": "did:web:alice.yourdomain.com",
  "verificationMethod": [
    {
      "id": "did:web:alice.yourdomain.com#key-0",
      "type": "JsonWebKey2020",
      "controller": "did:web:alice.yourdomain.com",
      "publicKeyJwk": {
        "kty": "EC",
        "crv": "P-256",
        "x": "PUBLIC_KEY_X_COMPONENT",
        "y": "PUBLIC_KEY_Y_COMPONENT"
      }
    }
  ],
  "authentication": [
    "did:web:alice.yourdomain.com#key-0"
  ],
  "assertionMethod": [
    "did:web:alice.yourdomain.com#key-0"
  ]
}
```

4. **Generate Key Pairs**
   - For each agent, generate ECDSA key pairs (P-256 curve)
   - Store private keys securely
   - Update the respective `did.json` files with public key components

### AT PROTOCOL REPOSITORY SETUP

1. **PDS Configuration**
   - Set up a minimal Personal Data Server (PDS) for each agent
   - Configure with the corresponding DID and private key
   - Basic PDS implementation requires:
     - Repository storage (can be file-based for prototype)
     - XRPC endpoint handler
     - Basic lexicon support for `com.atproto.*` endpoints

2. **Repository Initialization**
   - Initialize an empty repository for each agent
   - Add basic profile information records
   - Implement the minimal set of required PDS endpoints:
     - `com.atproto.server.getSession`
     - `com.atproto.repo.createRecord`
     - `com.atproto.repo.getRecord`

3. **Handle Registration**
   - Register each subdomain as a handle in the AT Protocol network
   - Verify the handle by hosting the appropriate verification endpoints

### BLUESKY INTEGRATION (OPTIONAL)

1. **Create Bluesky Accounts**
   - Obtain Bluesky invites if needed
   - Create accounts with temporary handles

2. **Handle Migration**
   - Migrate temporary handles to your custom domain handles
   - Follow the Bluesky handle migration process

3. **API Integration**
   - Configure authentication for the Bluesky API
   - Test basic operations (reading timeline, posting)

### NEXT STEPS

- Implement the local Ollama-based Alice agent
- Set up a simple HTTP server for AT Protocol interactions
- Begin implementing the Agora Protocol adapters
- Test basic communication between Alice and DelveLLM

### NOTES

- The AT Protocol identity system uses both DIDs and handles
- DIDs provide the cryptographic identity foundation
- Handles provide human-readable addresses
- For testing, you can use the did:plc method instead of did:web if domain setup is a blocker
- All AT Protocol interactions require proper digital signatures

## 2025-03-17 - Hosting Provider Migration

### OBJECTIVE
Migrate from DreamHost to a more developer-friendly hosting solution for our AT Protocol implementation.

### DIGITAL OCEAN SETUP

1. **Selected DigitalOcean as New Provider**
   - Chose the $4/month droplet (1 CPU, 1GB RAM, 10GB SSD, 500GB transfer)
   - Ubuntu 22.04 LTS for long-term stability
   - Set up SSH key authentication for secure access

2. **Web Server Configuration**
   - Installed Nginx for handling multiple subdomains
   - Created wildcard configuration for all *.cred.at subdomains
   - Configured subdomain directory structure in /var/www/
   - Verified working setup for alice.cred.at, bob.cred.at, delve.cred.at

3. **DNS Configuration**
   - Set up A record for cred.at root domain
   - Added wildcard DNS record (*.cred.at) pointing to our droplet IP
   - Confirmed DNS propagation via dig and curl testing

### ADVANTAGES OVER PREVIOUS HOSTING

- Much more direct control over server configuration
- Simpler, more developer-friendly interface
- SSH and command-line access without restrictions
- Better performance for same or lower cost
- Easy scalability if project requirements grow
- Wildcard subdomain support for AT Protocol identity architecture

### NEXT STEPS

- Add SSL/TLS certificates via Let's Encrypt
- Deploy our AT Protocol implementation
- Set up proper app server for running Python backend
- Configure environment for agent instances
