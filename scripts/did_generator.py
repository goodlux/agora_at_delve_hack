#!/usr/bin/env python3
"""
AT Protocol DID Generator

This script generates the cryptographic keys and DID documents needed
for AT Protocol agent identities.
"""

import os
import json
from pathlib import Path
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from datetime import datetime

class DIDGenerator:
    """Generate DIDs and key pairs for AT Protocol integration"""
    
    def __init__(self, domain, output_dir=None):
        """
        Initialize the DID generator.
        
        Args:
            domain (str): The base domain for your agents (e.g., 'cred.at')
            output_dir (str, optional): Directory to output the generated files
        """
        self.domain = domain
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "did_config"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def generate_key_pair(self):
        """
        Generate an ECDSA key pair (P-256 curve).
        
        Returns:
            dict: Dictionary containing private key and public key components
        """
        private_key = ec.generate_private_key(
            ec.SECP256R1(),  # P-256 curve
            default_backend()
        )
        
        # Get the public key
        public_key = private_key.public_key()
        
        # Serialize the private key to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get the public key in JWK format
        public_numbers = public_key.public_numbers()
        
        # Return key components
        return {
            "privateKey": private_pem.decode('utf-8'),
            "publicKey": {
                "x": self._int_to_base64url(public_numbers.x),
                "y": self._int_to_base64url(public_numbers.y)
            }
        }
    
    def _int_to_base64url(self, value):
        """Convert an integer to base64url encoding (required for JWK format)"""
        # Convert int to 32-byte big-endian representation
        byte_data = value.to_bytes(32, byteorder='big')
        # Encode as base64 and convert to base64url
        b64 = base64.b64encode(byte_data).decode('ascii')
        return b64.replace('+', '-').replace('/', '_').rstrip('=')
    
    def create_did_json(self, subdomain, key_pair):
        """
        Create a did.json file for a subdomain.
        
        Args:
            subdomain (str): The subdomain for the agent (e.g., 'alice')
            key_pair (dict): The key pair generated for this agent
            
        Returns:
            dict: The DID document as a dictionary
        """
        full_domain = f"{subdomain}.{self.domain}"
        did_json = {
            "@context": [
                "https://www.w3.org/ns/did/v1"
            ],
            "id": f"did:web:{full_domain}",
            "verificationMethod": [
                {
                    "id": f"did:web:{full_domain}#key-0",
                    "type": "JsonWebKey2020",
                    "controller": f"did:web:{full_domain}",
                    "publicKeyJwk": {
                        "kty": "EC",
                        "crv": "P-256",
                        "x": key_pair["publicKey"]["x"],
                        "y": key_pair["publicKey"]["y"]
                    }
                }
            ],
            "authentication": [
                f"did:web:{full_domain}#key-0"
            ],
            "assertionMethod": [
                f"did:web:{full_domain}#key-0"
            ]
        }
        
        # Create output directory
        subdomain_dir = self.output_dir / subdomain / ".well-known"
        subdomain_dir.mkdir(exist_ok=True, parents=True)
        
        # Write did.json
        with open(subdomain_dir / "did.json", 'w') as f:
            json.dump(did_json, f, indent=2)
        
        # Save private key to a separate file
        with open(self.output_dir / f"{subdomain}_private_key.pem", 'w') as f:
            f.write(key_pair["privateKey"])
        
        print(f"Created DID document for {full_domain}")
        print(f"  - DID document: {subdomain_dir / 'did.json'}")
        print(f"  - Private key: {self.output_dir / f'{subdomain}_private_key.pem'}")
        
        return did_json
    
    def generate_agent_config(self, agent_name):
        """
        Generate full configuration for an agent.
        
        Args:
            agent_name (str): The name of the agent (e.g., 'alice')
            
        Returns:
            dict: Complete agent configuration
        """
        subdomain = agent_name.lower()
        
        # Generate key pair
        key_pair = self.generate_key_pair()
        
        # Create DID JSON
        did_json = self.create_did_json(subdomain, key_pair)
        
        # Create agent config
        agent_config = {
            "name": agent_name,
            "did": did_json["id"],
            "handle": f"{subdomain}.{self.domain}",
            "privateKey": key_pair["privateKey"],
            "publicKey": key_pair["publicKey"],
            "created": datetime.utcnow().isoformat()
        }
        
        # Save agent config
        with open(self.output_dir / f"{agent_name.lower()}_config.json", 'w') as f:
            json.dump(agent_config, f, indent=2)
        
        print(f"Generated configuration for agent: {agent_name}")
        print(f"  - Config file: {self.output_dir / f'{agent_name.lower()}_config.json'}")
        
        return agent_config
    
    def create_deployment_guide(self, agents):
        """
        Create a guide for deploying the DID documents to a web server.
        
        Args:
            agents (list): List of agent names that were configured
        """
        guide = f"""# AT Protocol Agent Deployment Guide

This guide outlines the steps to deploy the DID documents for your AT Protocol agents.

## DID Documents

The following DID documents need to be hosted on your web server:

"""
        
        for agent in agents:
            subdomain = agent.lower()
            full_domain = f"{subdomain}.{self.domain}"
            guide += f"""
### {agent} Agent
* DID: `did:web:{full_domain}`
* File path: `{subdomain}/.well-known/did.json`
* URL: `https://{full_domain}/.well-known/did.json`

"""
        
        guide += """
## Apache Configuration

Here's a sample Apache virtual host configuration for your agents:

```apache
<VirtualHost *:80>
    ServerName alice.cred.at
    DocumentRoot /path/to/alice
    
    <Directory /path/to/alice>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName alice.cred.at
    DocumentRoot /path/to/alice
    
    <Directory /path/to/alice>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    SSLCertificateChainFile /path/to/chain.crt
</VirtualHost>

<VirtualHost *:80>
    ServerName delve.cred.at
    DocumentRoot /path/to/delve
    
    <Directory /path/to/delve>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName delve.cred.at
    DocumentRoot /path/to/delve
    
    <Directory /path/to/delve>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    SSLCertificateChainFile /path/to/chain.crt
</VirtualHost>
```

## SSL Certificates

You can obtain free SSL certificates using Let's Encrypt:

```bash
sudo apt update
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d alice.cred.at -d delve.cred.at
```

## Deployment Steps

1. Set up your DNS records to point to your server IP:
   * `alice.cred.at` → Your server IP
   * `delve.cred.at` → Your server IP

2. Upload the DID documents to your server:
   ```bash
   # Create directories
   mkdir -p /path/to/alice/.well-known
   mkdir -p /path/to/delve/.well-known
   
   # Copy DID documents
   cp alice/.well-known/did.json /path/to/alice/.well-known/
   cp delve/.well-known/did.json /path/to/delve/.well-known/
   ```

3. Configure Apache as shown above

4. Obtain SSL certificates

5. Test your configuration:
   ```bash
   curl https://alice.cred.at/.well-known/did.json
   curl https://delve.cred.at/.well-known/did.json
   ```

## Security Notes

* Keep your private keys secure and do not share them
* Ensure only authorized personnel can access your server
* Regularly update your server and software
"""
        
        guide_path = self.output_dir / "deployment_guide.md"
        with open(guide_path, 'w') as f:
            f.write(guide)
        
        print(f"Created deployment guide: {guide_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate DIDs and key pairs for AT Protocol agents")
    parser.add_argument("domain", help="Base domain for agents (e.g., 'cred.at')")
    parser.add_argument("--agents", nargs="+", default=["alice", "delve"], 
                       help="Agent names (default: alice delve)")
    parser.add_argument("--output", help="Output directory for generated files")
    
    args = parser.parse_args()
    
    generator = DIDGenerator(args.domain, args.output)
    
    print(f"Generating DID documents for domain: {args.domain}")
    print(f"Agents: {', '.join(args.agents)}")
    print()
    
    # Generate configs for all agents
    agent_configs = []
    for agent in args.agents:
        generator.generate_agent_config(agent)
        print()
    
    # Create deployment guide
    generator.create_deployment_guide(args.agents)


if __name__ == "__main__":
    main()