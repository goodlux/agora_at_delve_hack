#!/usr/bin/env python3
"""
Example: Setting Up Agora-AT Integration

This script demonstrates how to set up the integration between Agora Protocol
and AT Protocol using the enhanced adapters and bridge.
"""

import os
import json
import logging
import asyncio
from pathlib import Path

from agora_at.core.models import Agent, AgentCapability
from agora_at.core.bridge import ProtocolBridge
from agora_at.adapters.agora_adapter import AgoraAdapter
from agora_at.adapters.atproto_adapter import ATProtoAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("example-setup")


async def main():
    # Load the agent configurations
    config_dir = Path("did_config")
    
    # Load Alice agent config
    with open(config_dir / "alice_config.json", 'r') as f:
        alice_config = json.load(f)
    
    # Create Alice agent object
    alice_agent = Agent(
        did=alice_config["did"],
        handle=alice_config["handle"],
        capabilities=[
            AgentCapability.READ_PUBLIC,
            AgentCapability.WRITE_POSTS,
            AgentCapability.GENERATE_FEEDS
        ],
        endpoint="http://localhost:8000",  # Local agent endpoint
        description="Alice agent for Agora-AT integration"
    )
    
    # Load Delve agent config
    with open(config_dir / "delve_config.json", 'r') as f:
        delve_config = json.load(f)
    
    # Create Delve agent object
    delve_agent = Agent(
        did=delve_config["did"],
        handle=delve_config["handle"],
        capabilities=[
            AgentCapability.READ_PUBLIC,
            AgentCapability.MODERATE_CONTENT,
            AgentCapability.INTERACT_USERS
        ],
        endpoint="https://api.delvellm.com/agora",  # Remote API endpoint
        description="Delve agent for content processing"
    )
    
    # Initialize the protocol bridge
    bridge = ProtocolBridge(
        agora_agent=alice_agent,  # Alice is our Agora agent
        atproto_agent=alice_agent,  # Alice is also our AT Protocol identity
        atproto_service_url="https://bsky.social",  # Bluesky API endpoint
        config_dir=str(config_dir)
    )
    
    # Register callback for monitoring bridge messages
    bridge.on("on_message", lambda data: logger.info(f"Bridge message: {data['direction']}"))
    
    # Authenticate with AT Protocol
    # In a real app, you'd get these from environment variables or a secure store
    handle = "alice.cred.at"
    password = "your-secure-password"  # This is just a placeholder
    
    try:
        # Login to AT Protocol
        logger.info(f"Logging in as {handle}...")
        session = await bridge.login_atproto(handle, password)
        logger.info(f"Logged in successfully as {session['did']}")
        
        # Negotiate a protocol for social posts
        logger.info("Negotiating post creation protocol...")
        post_protocol = await bridge.negotiate_protocol(
            "Protocol for creating and formatting social media posts with rich text formatting",
            "post"
        )
        logger.info(f"Negotiated protocol: {post_protocol.id}")
        
        # Negotiate a protocol for feed processing
        logger.info("Negotiating feed processing protocol...")
        feed_protocol = await bridge.negotiate_protocol(
            "Protocol for efficiently processing and analyzing social media feeds",
            "process_feed"
        )
        logger.info(f"Negotiated protocol: {feed_protocol.id}")
        
        # Create a post through the bridge
        logger.info("Creating a test post...")
        post_result = await bridge.post_to_atproto(
            "Hello from the Agora-AT Protocol bridge! This post was created through the integration."
        )
        logger.info(f"Post created: {post_result.get('uri', 'unknown')}")
        
        # Get a feed and process it with the Agora agent
        logger.info("Getting feed data...")
        feed = await bridge.get_feed(limit=10)
        logger.info(f"Retrieved {len(feed)} feed items")
        
        logger.info("Processing feed with Agora agent...")
        feed_analysis = await bridge.process_feed_with_agora(
            feed_items=feed,
            task_description="Analyze the sentiment and topics of these posts"
        )
        logger.info(f"Feed analysis complete")
        logger.info(f"Top topics: {feed_analysis.get('topics', [])}")
        logger.info(f"Overall sentiment: {feed_analysis.get('sentiment', 'neutral')}")
        
        # Summarize the bridge capabilities
        bridge_info = bridge.summarize_capabilities()
        logger.info(f"Bridge capabilities: {json.dumps(bridge_info, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in example: {e}")
    
    logger.info("Example completed")


if __name__ == "__main__":
    asyncio.run(main())