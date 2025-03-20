# CLAUDE REFERENCE GUIDE

This document contains filesystem locations for quick reference when working with Claude.

## Repository Locations

### Agora Protocol
- Main repository: `/Users/rob/repos/agora-protocol`
- Python implementation: `/Users/rob/repos/agora-protocol/python`
- Documentation: `/Users/rob/repos/agora-protocol/website-v2/docs`
- Paper demo: `/Users/rob/repos/agora-protocol/paper-demo`

### AT Protocol
- Main repository: `/Users/rob/repos/atproto`
- Lexicon definitions: `/Users/rob/repos/atproto/lexicons`
- Core packages: `/Users/rob/repos/atproto/packages`
- Services: `/Users/rob/repos/atproto/services`

### AT Protocol Documentation
- Website repository: `/Users/rob/repos/atproto-website`
- Specifications: `/Users/rob/repos/atproto-website/src/app/[locale]/specs`
- Guides: `/Users/rob/repos/atproto-website/src/app/[locale]/guides`

### Agora-AT Integration (This Project)
- Main folder: `/Users/rob/repos/agora_at_delve_hack`
- Documentation: `/Users/rob/repos/agora_at_delve_hack/docs`
- Python implementation: `/Users/rob/repos/agora_at_delve_hack/agora_at`
- Examples: `/Users/rob/repos/agora_at_delve_hack/examples`

## Key Files

### Agora Protocol
- Core implementation: `/Users/rob/repos/agora-protocol/python/core.py`
- Main documentation: `/Users/rob/repos/agora-protocol/website-v2/docs/intro.md`

### AT Protocol
- Main README: `/Users/rob/repos/atproto/README.md`
- Protocol specification: `/Users/rob/repos/atproto-website/src/app/[locale]/specs/atp/en.mdx`
- Protocol overview: `/Users/rob/repos/atproto-website/src/app/[locale]/guides/overview/en.mdx`

### Agora-AT Integration
- Hackathon project ideas: `/Users/rob/repos/agora_at_delve_hack/docs/hackathon_projects.md`
- Core models: `/Users/rob/repos/agora_at_delve_hack/agora_at/core/models.py`
- AT Protocol adapter: `/Users/rob/repos/agora_at_delve_hack/agora_at/adapters/atproto_adapter.py`
- Agora adapter: `/Users/rob/repos/agora_at_delve_hack/agora_at/adapters/agora_adapter.py`

## Newly Developed Components

### 1. DID Generator (`did_generator.py`)
- Purpose: Generates cryptographic keys and DID documents for AT Protocol agents
- Features:
  - Creates secure ECDSA key pairs (P-256 curve)
  - Generates properly formatted DID documents
  - Produces deployment guides and configuration files
  - Creates agent configuration JSON files

### 2. Enhanced Protocol Bridge (`agora_at/core/bridge.py`)
- Purpose: Connects Agora Protocol with AT Protocol
- Features:
  - Bidirectional message translation
  - Protocol negotiation and management
  - Session management for AT Protocol
  - Event-based callback system
  - Configuration persistence

### 3. Enhanced AT Protocol Adapter (`agora_at/adapters/atproto_adapter.py`)
- Purpose: Handles interactions with the AT Protocol network
- Features:
  - Authentication and session management
  - Post creation and retrieval
  - Feed and profile operations
  - Error handling and logging
  - Protocol translation

### 4. Enhanced Agora Protocol Adapter (`agora_at/adapters/agora_adapter.py`)
- Purpose: Manages communication with Agora Protocol agents
- Features:
  - Protocol negotiation and storage
  - Message formatting and transmission
  - Content processing operations
  - Protocol statistics and optimization

### 5. Example Setup (`examples/example_setup.py`)
- Purpose: Demonstrates how to use the integration components
- Features:
  - Agent configuration loading
  - Protocol bridge setup
  - Protocol negotiation
  - Post creation and feed processing

## Next Steps

### 1. Server Setup
- Set up VPS on Dreamhost (already in progress)
- Get stable IP address for DNS configuration
- Configure Apache web server
- Set up SSH access for deployment

### 2. Domain and Identity Configuration
- Create DNS A records for subdomains:
  - `alice.cred.at` → VPS IP address
  - `delve.cred.at` → VPS IP address
- Run DID generator to create agent identities
- Deploy DID documents to web server
- Set up SSL certificates using Let's Encrypt

### 3. Agent Implementation
- Implement Ollama-based local agent (Alice)
- Set up SSH tunnel for local-to-server communication
- Configure vLLM endpoints for remote agents
- Implement the protocol bridge on the server

### 4. Protocol Testing
- Test basic communication between agents
- Test protocol negotiation
- Validate AT Protocol integration
- Measure efficiency improvements

### 5. Advanced Features
- Implement feed generation capabilities
- Add content moderation features
- Develop specialized protocol negotiation
- Create user interface for interaction

### Resources
- Current development log: `/Users/rob/repos/agora_at_delve_hack/docs/development_log.md`
- AT Protocol documentation: https://atproto.com/docs
- Bluesky documentation: https://bsky.social/about/api
- Agora Protocol documentation: https://agora-protocol.org
