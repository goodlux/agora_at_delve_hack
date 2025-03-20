#!/usr/bin/env python3
"""
Example showing how to use DIDs with ATProtoAdapter
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the required modules
from agora_at.core.models import Agent, AgentCapability
from agora_at.adapters.atproto_adapter import ATProtoAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("did-adapter-example")

def load_agent_from_config(agent_name: str, config_dir: str = None) -> Agent:
    """
    Load an agent configuration and create an Agent object.
    
    Args:
        agent_name: Name of the agent (e.g., 'alice', 'bob')
        config_dir: Directory containing the agent configuration files
        
    Returns:
        Agent: The initialized Agent object
    """
    if config_dir is None:
        config_dir = os.environ.get(
            'ATPROTO_KEY_PATH', 
            os.path.expanduser('~/secure_location/agora_at_keys')
        )
    
    config_path = os.path.join(config_dir, f"{agent_name}_config.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Agent configuration not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create agent with capabilities
    agent = Agent(
        did=config['did'],
        handle=config['handle'],
        capabilities=[
            AgentCapability.READ_PUBLIC,
            AgentCapability.WRITE_POSTS
        ],
        endpoint=f"https://{config['handle']}",
        description=f"{config['name']} Agent"
    )
    
    logger.info(f"Loaded agent {agent.handle} with DID {agent.did}")
    return agent

async def main():
    # Load an agent from configuration
    try:
        agent_name = "alice"  # Can be changed to any of your agents
        agent = load_agent_from_config(agent_name)
        
        # Initialize the AT Protocol adapter with the agent
        adapter = ATProtoAdapter(
            service_url="https://bsky.social",
            agent=agent
        )
        
        # Test signing functionality
        test_data = b"Hello, this is a test message"
        signature = adapter.sign_data(test_data)
        
        logger.info(f"Successfully signed data with {agent.handle}'s key")
        logger.info(f"Signature: {signature[:30]}...")
        
        # The adapter is now ready to be used with the agent's DID
        # From here, you could log in, create posts, etc.
        
        # Example of how you would use it in a real application:
        # await adapter.login(agent.handle, "your_password_here")
        # await adapter.create_post("Hello from my DID-authenticated agent!")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
