# Agora-AT Python Library

This Python library provides tools for integrating the Agora Protocol with the AT Protocol (ATProto).

## Structure

- `core/`: Core models and components
- `adapters/`: Protocol-specific adapters
- `services/`: Higher-level services built on the integration

## Usage

The library provides adapters for both protocols and a bridge to translate between them:

```python
from agora_at.core.models import Agent, AgentCapability
from agora_at.core.bridge import ProtocolBridge

# Define agents
alice_agent = Agent(
    did="did:plc:alice123",
    handle="alice.bsky.social",
    capabilities=[
        AgentCapability.READ_PUBLIC,
        AgentCapability.WRITE_POSTS
    ],
    endpoint="https://alice-agent.example.com",
    description="User-facing coordinator agent"
)

# Create a protocol bridge
bridge = ProtocolBridge(
    agora_agent=alice_agent,
    atproto_agent=alice_agent,  # Same identity for both sides
    atproto_service_url="https://bsky.social"
)

# Authenticate with AT Protocol
bridge.login_atproto("alice.bsky.social", "password")

# Negotiate efficient protocols
post_protocol = bridge.negotiate_protocol(
    "Efficient protocol for creating and formatting social media posts"
)

# Register protocol for message types
bridge.register_protocol("create_post", post_protocol)

# Send messages across protocols
result = bridge.send_to_atproto({
    "type": "post",
    "text": "Hello from Agora Protocol!"
})
```

## Development

This library is in active development for the Agora-AT integration project.
