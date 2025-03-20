#!/usr/bin/env python3
"""
Delve Bot for Bluesky

This script creates a Bluesky bot that uses the Delve DID to authenticate
and interact with users on the platform.
"""

import os
import sys
import json
import logging
import asyncio
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Add the package to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the required modules
from agora_at.core.models import Agent, AgentCapability
from agora_at.adapters.atproto_adapter import ATProtoAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("delve_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("delve-bot")

# Configuration
BLUESKY_SERVICE = "https://bsky.social"
CHECK_INTERVAL = 60  # seconds
AGENT_NAME = "delve"
MAX_MENTIONS_TO_PROCESS = 10

class DelveBot:
    """
    Bluesky bot for the Delve agent.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Delve Bluesky bot.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.agent = None
        self.adapter = None
        self.config = self._load_config(config_path)
        self.last_check_time = datetime.now(timezone.utc) - timedelta(hours=24)
        self.setup()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict containing configuration
        """
        # Default configuration
        config = {
            "agent_name": AGENT_NAME,
            "bluesky_service": BLUESKY_SERVICE,
            "check_interval": CHECK_INTERVAL,
            "secure_key_path": os.environ.get(
                'ATPROTO_KEY_PATH', 
                os.path.expanduser('~/secure_location/agora_at_keys')
            )
        }
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        return config
    
    def setup(self):
        """
        Set up the agent and adapter.
        """
        try:
            # Load agent configuration
            agent_config_path = os.path.join(
                self.config["secure_key_path"],
                f"{self.config['agent_name']}_config.json"
            )
            
            with open(agent_config_path, 'r') as f:
                agent_config = json.load(f)
            
            # Create agent
            self.agent = Agent(
                did=agent_config["did"],
                handle=agent_config["handle"],
                capabilities=[
                    AgentCapability.READ_PUBLIC,
                    AgentCapability.WRITE_POSTS
                ],
                endpoint=f"https://{agent_config['handle']}",
                description=f"Delve Agent - A bridge between Agora and AT Protocol"
            )
            
            # Create adapter
            self.adapter = ATProtoAdapter(
                service_url=self.config["bluesky_service"],
                agent=self.agent
            )
            
            logger.info(f"Set up Delve bot with DID: {self.agent.did}")
            
        except Exception as e:
            logger.error(f"Error setting up bot: {e}")
            raise
    
    async def authenticate(self, app_password: str) -> bool:
        """
        Authenticate with Bluesky.
        
        Args:
            app_password: App password for Bluesky authentication
            
        Returns:
            True if authentication was successful
        """
        if not self.adapter:
            logger.error("Adapter not initialized")
            return False
        
        try:
            # Try to load existing session
            if hasattr(self.adapter, 'session') and self.adapter.session:
                logger.info("Using existing session")
                return True
            
            # Authenticate
            await self.adapter.login(self.agent.handle, app_password)
            logger.info(f"Successfully authenticated as {self.agent.handle}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def post_message(self, text: str) -> Dict[str, Any]:
        """
        Post a message to Bluesky.
        
        Args:
            text: Text content of the post
            
        Returns:
            Post creation result
        """
        if not self.adapter:
            raise Exception("Adapter not initialized")
        
        try:
            result = await self.adapter.create_post(text)
            logger.info(f"Posted message: {text[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error posting message: {e}")
            raise
    
    async def check_mentions(self) -> List[Dict[str, Any]]:
        """
        Check for mentions of the bot.
        
        Returns:
            List of posts mentioning the bot
        """
        if not self.adapter or not self.adapter.session:
            logger.error("Not authenticated")
            return []
        
        try:
            # Convert last check time to ISO format
            since = self.last_check_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Search for mentions
            # Note: This is a simplified approach; the real implementation
            # would need to handle Bluesky's specific mention mechanism
            query = f"@{self.agent.handle}"
            posts = await self.adapter.search_posts(query)
            
            # Filter by time
            recent_posts = [
                post for post in posts
                if datetime.fromisoformat(post.get("indexedAt", "").replace("Z", "+00:00")) > self.last_check_time
                and post.get("author", {}).get("handle") != self.agent.handle  # Exclude self-mentions
            ]
            
            # Update last check time
            self.last_check_time = datetime.now(timezone.utc)
            
            logger.info(f"Found {len(recent_posts)} new mentions")
            return recent_posts[:MAX_MENTIONS_TO_PROCESS]  # Limit to avoid overload
            
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            return []
    
    async def process_mention(self, post: Dict[str, Any]) -> None:
        """
        Process a mention and respond if appropriate.
        
        Args:
            post: Post data containing the mention
        """
        if not post:
            return
        
        try:
            # Extract relevant information
            author = post.get("author", {}).get("handle", "unknown")
            content = post.get("record", {}).get("text", "")
            
            logger.info(f"Processing mention from {author}: {content[:50]}...")
            
            # Simple response for now
            response = self.generate_response(content, author)
            
            # Add reply link
            post_uri = post.get("uri", "")
            if post_uri:
                # Here you would add the facets/reply information
                # This is a simplified version
                pass
            
            # Post the response
            await self.post_message(response)
            
        except Exception as e:
            logger.error(f"Error processing mention: {e}")
    
    def generate_response(self, content: str, author: str) -> str:
        """
        Generate a response to a mention.
        
        Args:
            content: Content of the mention
            author: Author of the mention
            
        Returns:
            Generated response
        """
        # Simple response for now
        # In a real implementation, this would integrate with your AI/LLM
        greetings = [
            "Hello", "Hi", "Hey", "Greetings", "Hello there"
        ]
        
        responses = [
            "I'm Delve, a bridge between Agora and AT Protocol.",
            "Thanks for reaching out! I'm still learning, but I'll do my best to help.",
            "I'm an experimental bot that connects different agent networks.",
            "I'm just getting started on Bluesky. How can I assist you today?"
        ]
        
        greeting = random.choice(greetings)
        response = random.choice(responses)
        
        return f"{greeting} @{author}! {response}"
    
    async def run_once(self) -> None:
        """
        Run one iteration of the bot loop.
        """
        logger.info("Running bot iteration...")
        
        # Check for mentions
        mentions = await self.check_mentions()
        
        # Process each mention
        for mention in mentions:
            await self.process_mention(mention)
    
    async def run(self) -> None:
        """
        Run the bot in a continuous loop.
        """
        logger.info("Starting Delve Bluesky bot...")
        
        while True:
            try:
                await self.run_once()
                
                # Sleep until next check
                logger.info(f"Sleeping for {self.config['check_interval']} seconds...")
                await asyncio.sleep(self.config["check_interval"])
                
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                # Sleep for a bit before retrying
                await asyncio.sleep(30)

async def main():
    # Get app password from environment or prompt
    app_password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not app_password:
        import getpass
        app_password = getpass.getpass("Enter Bluesky app password for Delve: ")
    
    # Initialize and run the bot
    bot = DelveBot()
    authenticated = await bot.authenticate(app_password)
    
    if authenticated:
        # Post initial message
        await bot.post_message("Hello Bluesky! I'm Delve, a bridge between Agora and AT Protocol. I'm just getting started, but I'll be monitoring mentions and helping out where I can. #AgentNetworks #AIAssistant")
        
        # Run the bot
        await bot.run()
    else:
        logger.error("Failed to authenticate. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())
