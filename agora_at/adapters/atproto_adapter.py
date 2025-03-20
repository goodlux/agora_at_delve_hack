# agora_at/adapters/atproto_adapter.py
"""
Enhanced Adapter for AT Protocol integration with Agora agents
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.backends import default_backend

from ..core.models import Agent, AgentCapability, BridgeMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("atproto-adapter")


class ATProtoAdapter:
    """
    Adapter for AT Protocol services to interact with Agora agents.
    """
    
    def __init__(self, service_url: str, agent: Agent, config_dir: Optional[str] = None):
        """
        Initialize the AT Protocol adapter.
        
        Args:
            service_url: URL of the AT Protocol service (e.g. 'https://bsky.social')
            agent: Agent identity information
            config_dir: Optional directory for session storage
        """
        self.service_url = service_url
        self.agent = agent
        self.session = None
        self.config_dir = config_dir or os.path.expanduser("~/.agora_at")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Try to load saved session
        self._load_session()
        
        logger.info(f"Initialized AT Protocol adapter for {agent.did}")

    def _load_private_key(self, pem_data: str) -> ec.EllipticCurvePrivateKey:
        """Load a private key from PEM format"""
        try:
            return serialization.load_pem_private_key(
                pem_data.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            raise ValueError(f"Invalid private key format: {e}")

    def sign_data(self, data: bytes) -> str:
        """Sign data using the agent's private key"""
        try:
            # Load private key if needed
            if not hasattr(self, 'private_key'):
                # Get agent name from the handle or DID
                agent_name = self.agent.handle.split('.')[0] if self.agent.handle else self.agent.did.split(':')[-1].split('.')[0]
                
                private_key_path = os.path.join(
                    os.environ.get('ATPROTO_KEY_PATH', os.path.expanduser('~/secure_location/agora_at_keys')),
                    f"{agent_name.lower()}_private_key.pem"
                )
                with open(private_key_path, 'r') as f:
                    private_key_data = f.read()
                self.private_key = self._load_private_key(private_key_data)
            
            # Hash the data
            digest = hashes.Hash(hashes.SHA256())
            digest.update(data)
            data_hash = digest.finalize()
            
            # Sign the hash
            signature = self.private_key.sign(
                data_hash,
                ec.ECDSA(utils.Prehashed(hashes.SHA256()))
            )
            
            # Encode to base64
            return base64.b64encode(signature).decode('ascii')
            
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            raise
        
    
    def _get_session_path(self) -> str:
        """Get the path to the session file"""
        # Use the DID as part of the filename to support multiple agents
        agent_id = self.agent.did.split(":")[-1].replace(".", "_")
        return os.path.join(self.config_dir, f"atproto_session_{agent_id}.json")
    
    def _load_session(self) -> None:
        """Load saved session from disk"""
        session_path = self._get_session_path()
        
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r') as f:
                    self.session = json.load(f)
                
                logger.info(f"Loaded AT Protocol session for {self.agent.did}")
            except Exception as e:
                logger.error(f"Error loading session: {e}")
    
    def _save_session(self) -> None:
        """Save session to disk"""
        if self.session:
            session_path = self._get_session_path()
            
            try:
                with open(session_path, 'w') as f:
                    json.dump(self.session, f, indent=2)
                
                logger.info(f"Saved AT Protocol session for {self.agent.did}")
            except Exception as e:
                logger.error(f"Error saving session: {e}")
    
    async def login(self, handle: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the AT Protocol service.
        
        Args:
            handle: User handle or identifier
            password: Authentication password or token
            
        Returns:
            Session information
        """
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.post(
                    f"{self.service_url}/xrpc/com.atproto.server.createSession",
                    json={"identifier": handle, "password": password}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to authenticate: {error_text}")
                
                self.session = await response.json()
                self._save_session()
                
                logger.info(f"Successfully authenticated as {handle}")
                return self.session
                
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise
    
    async def refresh_session(self) -> bool:
        """
        Refresh the authentication session if needed.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.session or "refreshJwt" not in self.session:
            logger.warning("No refresh token available")
            return False
        
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.post(
                    f"{self.service_url}/xrpc/com.atproto.server.refreshSession",
                    headers={"Authorization": f"Bearer {self.session['refreshJwt']}"}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to refresh session: {error_text}")
                    return False
                
                self.session = await response.json()
                self._save_session()
                
                logger.info("Successfully refreshed session")
                return True
                
            except Exception as e:
                logger.error(f"Session refresh failed: {e}")
                return False
    
    def set_session(self, did: str, access_jwt: str, refresh_jwt: str) -> None:
        """
        Set an existing session.
        
        Args:
            did: DID of the user
            access_jwt: Access JWT token
            refresh_jwt: Refresh JWT token
        """
        self.session = {
            "did": did,
            "accessJwt": access_jwt,
            "refreshJwt": refresh_jwt
        }
        self._save_session()
    
    async def create_post(self, text: str, facets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create a post on the AT Protocol network.
        
        Args:
            text: Text content of the post
            facets: Optional rich text facets
            
        Returns:
            Post creation result
        """
        if not self.has_capability(AgentCapability.WRITE_POSTS):
            raise Exception("Agent does not have WRITE_POSTS capability")
            
        if not self.session:
            raise Exception("Not authenticated")
        
        record = {
            "text": text,
            "$type": "app.bsky.feed.post",
            "createdAt": self._get_iso_timestamp()
        }
        
        if facets:
            record["facets"] = facets
        
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.post(
                    f"{self.service_url}/xrpc/com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
                    json={
                        "repo": self.session["did"],
                        "collection": "app.bsky.feed.post",
                        "record": record
                    }
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to create post: {error_text}")
                
                result = await response.json()
                logger.info(f"Successfully created post: {result.get('uri', 'unknown')}")
                return result
                
            except Exception as e:
                logger.error(f"Error creating post: {e}")
                raise
    
    async def get_profile(self, actor: str) -> Dict[str, Any]:
        """
        Get a user's profile.
        
        Args:
            actor: Handle or DID of the user
            
        Returns:
            Profile information
        """
        if not self.has_capability(AgentCapability.READ_PUBLIC):
            raise Exception("Agent does not have READ_PUBLIC capability")
            
        if not self.session:
            raise Exception("Not authenticated")
        
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.get(
                    f"{self.service_url}/xrpc/app.bsky.actor.getProfile",
                    headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
                    params={"actor": actor}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get profile: {error_text}")
                
                return await response.json()
                
            except Exception as e:
                logger.error(f"Error getting profile: {e}")
                raise
    
    async def get_feed(self, algorithm: str = "reverse-chronological", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get posts from a timeline.
        
        Args:
            algorithm: Feed algorithm to use
            limit: Maximum number of posts to return
            
        Returns:
            List of posts
        """
        if not self.has_capability(AgentCapability.READ_PUBLIC):
            raise Exception("Agent does not have READ_PUBLIC capability")
            
        if not self.session:
            raise Exception("Not authenticated")
        
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.get(
                    f"{self.service_url}/xrpc/app.bsky.feed.getTimeline",
                    headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
                    params={"algorithm": algorithm, "limit": limit}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get feed: {error_text}")
                
                result = await response.json()
                return result.get("feed", [])
                
            except Exception as e:
                logger.error(f"Error getting feed: {e}")
                raise
    
    async def search_posts(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for posts.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching posts
        """
        if not self.has_capability(AgentCapability.READ_PUBLIC):
            raise Exception("Agent does not have READ_PUBLIC capability")
            
        if not self.session:
            raise Exception("Not authenticated")
        
        async with aiohttp.ClientSession() as http_session:
            try:
                response = await http_session.get(
                    f"{self.service_url}/xrpc/app.bsky.feed.searchPosts",
                    headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
                    params={"q": query, "limit": limit}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to search posts: {error_text}")
                
                result = await response.json()
                return result.get("posts", [])
                
            except Exception as e:
                logger.error(f"Error searching posts: {e}")
                raise
    
    async def process_bridge_message(self, message: BridgeMessage) -> Any:
        """
        Process a bridge message from Agora and translate it to AT Protocol.
        
        Args:
            message: Bridge message to process
            
        Returns:
            Processing result
        """
        if message.target != "atproto":
            raise ValueError("Message target must be atproto")
        
        content = message.content
        message_type = content.get("type", "")
        
        # Handle different message types
        if message_type == "post":
            return await self.create_post(content.get("text", ""), content.get("facets"))
        
        elif message_type == "get_feed":
            return await self.get_feed(content.get("algorithm"), content.get("limit", 50))
        
        elif message_type == "get_profile":
            return await self.get_profile(content.get("actor"))
        
        elif message_type == "search_posts":
            return await self.search_posts(content.get("query"), content.get("limit", 25))
        
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """
        Check if the agent has a specific capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if the agent has the capability
        """
        return capability in self.agent.capabilities
    
    def _get_iso_timestamp(self) -> str:
        """Get current time in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')