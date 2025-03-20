# DID Deployment Documentation

This document explains how to deploy Decentralized Identifiers (DIDs) for your AT Protocol agents to your Digital Ocean server.

## What Are DIDs?

Decentralized Identifiers (DIDs) are a new type of identifier that enables verifiable, decentralized digital identity. In the AT Protocol, DIDs serve as the cryptographic foundation for agent identities. Each agent has:

1. A DID (like `did:web:alice.cred.at`)
2. A human-readable handle (like `alice.cred.at`)
3. A key pair for digital signatures and authentication

## Deployment Script

The `deploy-dids.sh` script automates the process of:

1. Generating DIDs and cryptographic keys
2. Creating the necessary server directory structure
3. Uploading the DID documents to your server
4. Configuring Nginx to serve these files correctly
5. (Optionally) Setting up SSL certificates

### Prerequisites

- Python 3.7+ with the `cryptography` package installed
- SSH access to your Digital Ocean server
- Nginx installed on your server

### Using the Script

1. Make the script executable:
   ```bash
   chmod +x deploy-dids.sh
   ```

2. Run the script from your project root directory:
   ```bash
   ./deploy-dids.sh
   ```

3. For additional options:
   ```bash
   ./deploy-dids.sh --install-deps --setup-ssl
   ```

   Options:
   - `--install-deps`: Install dependencies on the remote server (Nginx)
   - `--setup-ssl`: Set up SSL certificates with Let's Encrypt

### What the Script Does

1. **DID Generation**:
   - Uses `did_generator.py` to create DIDs and key pairs
   - Generates a DID document for each agent
   - Creates configuration files with public and private keys

2. **Server Configuration**:
   - Creates `.well-known` directories for each agent on your server
   - Uploads the DID documents to these directories
   - Configures Nginx to serve the DID documents correctly

3. **SSL Configuration** (if `--setup-ssl` is used):
   - Installs Let's Encrypt's Certbot
   - Obtains SSL certificates for all domains
   - Configures Nginx to use HTTPS

4. **Backup and Security**:
   - Backs up private keys and configuration files locally
   - Sets appropriate permissions on the server

## Manual Verification

After running the script, you should be able to access your DID documents at:

```
https://alice.cred.at/.well-known/did.json
https://bob.cred.at/.well-known/did.json
https://charlie.cred.at/.well-known/did.json
https://delve.cred.at/.well-known/did.json
```

Or via HTTP if SSL is not configured:

```
http://alice.cred.at/.well-known/did.json
http://bob.cred.at/.well-known/did.json
http://charlie.cred.at/.well-known/did.json
http://delve.cred.at/.well-known/did.json
```

## DID Document Structure

Each DID document follows this standard format:

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1"
  ],
  "id": "did:web:alice.cred.at",
  "verificationMethod": [
    {
      "id": "did:web:alice.cred.at#key-0",
      "type": "JsonWebKey2020",
      "controller": "did:web:alice.cred.at",
      "publicKeyJwk": {
        "kty": "EC",
        "crv": "P-256",
        "x": "PUBLIC_KEY_X_COMPONENT",
        "y": "PUBLIC_KEY_Y_COMPONENT"
      }
    }
  ],
  "authentication": [
    "did:web:alice.cred.at#key-0"
  ],
  "assertionMethod": [
    "did:web:alice.cred.at#key-0"
  ]
}
```

## Agent Configuration Files

The script also generates configuration files for each agent in JSON format:

```json
{
  "name": "Alice",
  "did": "did:web:alice.cred.at",
  "handle": "alice.cred.at",
  "privateKey": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "publicKey": {
    "x": "BASE64URL_ENCODED_X_COMPONENT",
    "y": "BASE64URL_ENCODED_Y_COMPONENT"
  },
  "created": "2025-03-17T12:34:56.789Z"
}
```

These files contain sensitive information and should be stored securely.

## Next Steps

After deploying your DIDs, you can:

1. Use the generated configuration files with your AT Protocol implementation
2. Configure your agents to use these identities
3. Start implementing the protocol bridge between Agora and AT Protocol
4. Begin testing communication between agents

## Security Considerations

1. **Private Key Storage**: The private keys are sensitive and should be stored securely. Consider using a secret management solution in production.

2. **Production Readiness**: This setup is suitable for development and testing. For production, additional security measures should be implemented.

3. **Key Rotation**: Consider implementing a key rotation strategy for long-term security.

4. **Backup**: Regularly back up your configuration files and private keys. If these are lost, you'll lose control of your agent identities.