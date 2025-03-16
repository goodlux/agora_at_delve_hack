"""
Adapter for AT Protocol integration with Agora agents
"""

import requests
from typing import Dict, Any, List, Optional
from ..core.models import Agent, AgentCapability, BridgeMessage


class ATProtoAdapter:
    """
    Adapter for AT Protocol services to interact with Agora agents.
    """
    
    def __init__(self, service_url: str, agent: Agent):
        """
        Initialize the AT Protocol adapter.
        
        Args:
            service_url: URL of the AT Protocol service
            agent: Agent identity information
        """
        self.service_url = service_url
        self.agent = agent
        self.session = None
    
    def login(self, handle: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the AT Protocol service.
        
        Args:
            handle: User handle or identifier
            password: Authentication password or token
            
        Returns:
            Session information
        """
        response = requests.post(
            f"{self.service_url}/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to authenticate: {response.text}")
        
        self.session = response.json()
        return self.session
    
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
    
    def create_post(self, text: str, facets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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
        
        response = requests.post(
            f"{self.service_url}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
            json={
                "repo": self.session["did"],
                "collection": "app.bsky.feed.post",
                "record": record
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create post: {response.text}")
        
        return response.json()
    
    def get_feed(self, algorithm: str = "reverse-chronological", limit: int = 50) -> List[Dict[str, Any]]:
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
        
        response = requests.get(
            f"{self.service_url}/xrpc/app.bsky.feed.getTimeline",
            headers={"Authorization": f"Bearer {self.session['accessJwt']}"},
            params={"algorithm": algorithm, "limit": limit}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get feed: {response.text}")
        
        return response.json().get("feed", [])
    
    def process_bridge_message(self, message: BridgeMessage) -> Any:
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
        
        # Handle different message types
        if content.get("type") == "post":
            return self.create_post(content.get("text", ""), content.get("facets"))
        
        elif content.get("type") == "get_feed":
            return self.get_feed(content.get("algorithm"), content.get("limit", 50))
        
        else:
            raise ValueError(f"Unsupported message type: {content.get('type')}")
    
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
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
