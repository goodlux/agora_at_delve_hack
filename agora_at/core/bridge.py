# agora_at/core/bridge.py
"""
Enhanced Protocol Bridge for connecting Agora Protocol and AT Protocol

This bridges communication between Agora Protocol agents and the AT Protocol
ecosystem, enabling agents to participate in decentralized social networks.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime

from ..core.models import Agent, BridgeMessage, NegotiatedProtocol, AgentCapability
from ..adapters.agora_adapter import AgoraAdapter
from ..adapters.atproto_adapter import ATProtoAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agora-at-bridge")


class ProtocolBridge:
    """
    Bridge for translating between Agora Protocol and AT Protocol.
    
    This class handles bidirectional communication between Agora agents
    and the AT Protocol network, providing:
    
    1. Protocol negotiation and translation
    2. Authentication and session management
    3. Content creation and retrieval
    4. Event callbacks for integration with other systems
    """
    
    def __init__(self, 
                 agora_agent: Agent, 
                 atproto_agent: Agent, 
                 atproto_service_url: str,
                 config_dir: Optional[str] = None):
        """
        Initialize the protocol bridge.
        
        Args:
            agora_agent: Agora agent identity
            atproto_agent: AT Protocol agent identity
            atproto_service_url: URL of the AT Protocol service
            config_dir: Optional directory for storing configuration and keys
        """
        self.agora_agent = agora_agent
        self.atproto_agent = atproto_agent
        self.atproto_service_url = atproto_service_url
        self.config_dir = config_dir or os.path.expanduser("~/.agora_at")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize adapters
        self.agora_adapter = AgoraAdapter(agora_agent)
        self.atproto_adapter = ATProtoAdapter(atproto_service_url, atproto_agent)
        
        # Mapping of message types to protocol handlers
        self.protocol_handlers = {}
        
        # Event callbacks
        self.callbacks = {
            "on_message": [],
            "on_post": [],
            "on_protocol_negotiated": [],
            "on_error": []
        }
        
        # Load existing protocols if available
        self._load_protocols()
        
        logger.info(f"Protocol bridge initialized for {agora_agent.did} <-> {atproto_agent.did}")
    
    def _load_protocols(self) -> None:
        """Load previously negotiated protocols from disk"""
        protocols_path = os.path.join(self.config_dir, "protocols.json")
        
        if os.path.exists(protocols_path):
            try:
                with open(protocols_path, 'r') as f:
                    protocol_data = json.load(f)
                
                for message_type, protocol in protocol_data.items():
                    self.protocol_handlers[message_type] = NegotiatedProtocol(
                        id=protocol["id"],
                        version=protocol["version"],
                        description=protocol["description"],
                        schema=protocol["schema"]
                    )
                
                logger.info(f"Loaded {len(protocol_data)} protocols from {protocols_path}")
            except Exception as e:
                logger.error(f"Error loading protocols: {e}")
    
    def _save_protocols(self) -> None:
        """Save negotiated protocols to disk"""
        protocols_path = os.path.join(self.config_dir, "protocols.json")
        
        protocol_data = {}
        for message_type, protocol in self.protocol_handlers.items():
            protocol_data[message_type] = {
                "id": protocol.id,
                "version": protocol.version,
                "description": protocol.description,
                "schema": protocol.schema
            }
        
        try:
            with open(protocols_path, 'w') as f:
                json.dump(protocol_data, f, indent=2)
            
            logger.info(f"Saved {len(protocol_data)} protocols to {protocols_path}")
        except Exception as e:
            logger.error(f"Error saving protocols: {e}")
    
    def register_protocol(self, message_type: str, protocol: NegotiatedProtocol) -> None:
        """
        Register a protocol for a specific message type.
        
        Args:
            message_type: Type of message
            protocol: Protocol to use for this message type
        """
        self.protocol_handlers[message_type] = protocol
        self._save_protocols()
        
        # Trigger callbacks
        self._trigger_callbacks("on_protocol_negotiated", {
            "message_type": message_type,
            "protocol": protocol
        })
    
    def on(self, event_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific event.
        
        Args:
            event_type: Type of event (on_message, on_post, on_protocol_negotiated, on_error)
            callback: Function to call when the event occurs
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Trigger callbacks for a specific event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in {event_type} callback: {e}")
    
    async def send_to_agora(self, message: Dict[str, Any], message_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message from AT Protocol to Agora Protocol.
        
        Args:
            message: Message content
            message_type: Optional message type for protocol selection
            
        Returns:
            Agent response
        """
        # Create bridge message
        bridge_message = BridgeMessage(
            source="atproto",
            target="agora",
            content=message,
            protocol=self.protocol_handlers.get(message_type) if message_type else None,
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "message_type": message_type
            }
        )
        
        # Trigger callbacks
        self._trigger_callbacks("on_message", {
            "direction": "to_agora",
            "message": message,
            "message_type": message_type
        })
        
        try:
            # Process through adapter
            response = await self.agora_adapter.process_bridge_message(bridge_message)
            return response
        except Exception as e:
            logger.error(f"Error sending message to Agora: {e}")
            self._trigger_callbacks("on_error", {
                "error": str(e),
                "direction": "to_agora",
                "message": message
            })
            raise
    
    async def send_to_atproto(self, message: Dict[str, Any], message_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message from Agora Protocol to AT Protocol.
        
        Args:
            message: Message content
            message_type: Optional message type for protocol selection
            
        Returns:
            Processing result
        """
        # Create bridge message
        bridge_message = BridgeMessage(
            source="agora",
            target="atproto",
            content=message,
            protocol=self.protocol_handlers.get(message_type) if message_type else None,
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "message_type": message_type
            }
        )
        
        # Trigger callbacks
        self._trigger_callbacks("on_message", {
            "direction": "to_atproto",
            "message": message,
            "message_type": message_type
        })
        
        try:
            # Process through adapter
            response = await self.atproto_adapter.process_bridge_message(bridge_message)
            
            # Special handling for posts
            if message_type == "post" or message.get("type") == "post":
                self._trigger_callbacks("on_post", {
                    "content": message.get("text", ""),
                    "response": response
                })
            
            return response
        except Exception as e:
            logger.error(f"Error sending message to AT Protocol: {e}")
            self._trigger_callbacks("on_error", {
                "error": str(e),
                "direction": "to_atproto",
                "message": message
            })
            raise
    
    async def negotiate_protocol(self, description: str, message_type: Optional[str] = None) -> NegotiatedProtocol:
        """
        Negotiate a new protocol with an Agora agent.
        
        Args:
            description: Description of the protocol to negotiate
            message_type: Optional message type to associate with this protocol
            
        Returns:
            The negotiated protocol
        """
        try:
            protocol = await self.agora_adapter.negotiate_protocol(description)
            
            # Register the protocol if a message type is provided
            if message_type:
                self.register_protocol(message_type, protocol)
            
            return protocol
        except Exception as e:
            logger.error(f"Error negotiating protocol: {e}")
            self._trigger_callbacks("on_error", {
                "error": str(e),
                "action": "negotiate_protocol",
                "description": description
            })
            raise
    
    async def login_atproto(self, handle: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the AT Protocol service.
        
        Args:
            handle: User handle or identifier
            password: Authentication password or token
            
        Returns:
            Session information
        """
        try:
            session = await self.atproto_adapter.login(handle, password)
            return session
        except Exception as e:
            logger.error(f"Error logging in to AT Protocol: {e}")
            self._trigger_callbacks("on_error", {
                "error": str(e),
                "action": "login_atproto",
                "handle": handle
            })
            raise
    
    async def post_to_atproto(self, text: str, facets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create a post on the AT Protocol network.
        
        Args:
            text: Text content of the post
            facets: Optional rich text facets
            
        Returns:
            Post creation result
        """
        if not self.atproto_adapter.has_capability(AgentCapability.WRITE_POSTS):
            raise ValueError("Agent does not have WRITE_POSTS capability")
        
        message = {
            "type": "post",
            "text": text
        }
        
        if facets:
            message["facets"] = facets
        
        return await self.send_to_atproto(message, "post")
    
    async def get_feed(self, algorithm: str = "reverse-chronological", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get posts from a timeline.
        
        Args:
            algorithm: Feed algorithm to use
            limit: Maximum number of posts to return
            
        Returns:
            List of posts
        """
        message = {
            "type": "get_feed",
            "algorithm": algorithm,
            "limit": limit
        }
        
        response = await self.send_to_atproto(message, "get_feed")
        return response.get("feed", [])
    
    async def process_feed_with_agora(self, feed_items: List[Dict[str, Any]], 
                                      task_description: str) -> Dict[str, Any]:
        """
        Process feed items with an Agora agent.
        
        Args:
            feed_items: List of feed items to process
            task_description: Description of the processing task
            
        Returns:
            Processing results
        """
        message = {
            "type": "process_feed",
            "feed_items": feed_items,
            "task_description": task_description
        }
        
        # Use an existing protocol if available, otherwise use natural language
        message_type = "process_feed" if "process_feed" in self.protocol_handlers else None
        
        return await self.send_to_agora(message, message_type)
    
    def summarize_capabilities(self) -> Dict[str, Any]:
        """
        Summarize the capabilities of the bridge.
        
        Returns:
            Summary of bridge capabilities
        """
        return {
            "agora_agent": {
                "did": self.agora_agent.did,
                "handle": self.agora_agent.handle,
                "capabilities": [c.value for c in self.agora_agent.capabilities],
                "endpoint": self.agora_agent.endpoint
            },
            "atproto_agent": {
                "did": self.atproto_agent.did,
                "handle": self.atproto_agent.handle,
                "capabilities": [c.value for c in self.atproto_agent.capabilities]
            },
            "negotiated_protocols": [
                {
                    "message_type": message_type,
                    "protocol_id": protocol.id,
                    "description": protocol.description
                }
                for message_type, protocol in self.protocol_handlers.items()
            ],
            "atproto_service": self.atproto_service_url,
            "authenticated": self.atproto_adapter.session is not None
        }