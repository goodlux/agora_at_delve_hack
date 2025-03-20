# agora_at/adapters/agora_adapter.py
"""
Enhanced Adapter for Agora Protocol integration with AT Protocol
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..core.models import Agent, NegotiatedProtocol, BridgeMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agora-adapter")


class AgoraAdapter:
    """
    Adapter for Agora Protocol agent communication.
    
    This adapter handles:
    1. Communication with Agora Protocol agents
    2. Protocol negotiation and management
    3. Translating between Agora and AT Protocol formats
    """
    
    def __init__(self, agent: Agent, config_dir: Optional[str] = None):
        """
        Initialize the Agora Protocol adapter.
        
        Args:
            agent: Agent identity information
            config_dir: Optional directory for protocol storage
        """
        self.agent = agent
        self.config_dir = config_dir or os.path.expanduser("~/.agora_at")
        self.protocols = {}  # Maps protocol IDs to protocol objects
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load existing protocols
        self._load_protocols()
        
        logger.info(f"Initialized Agora Protocol adapter for {agent.did}")
    
    def _get_protocols_path(self) -> str:
        """Get the path to the protocols file"""
        # Use the DID as part of the filename to support multiple agents
        agent_id = self.agent.did.split(":")[-1].replace(".", "_")
        return os.path.join(self.config_dir, f"agora_protocols_{agent_id}.json")
    
    def _load_protocols(self) -> None:
        """Load saved protocols from disk"""
        protocols_path = self._get_protocols_path()
        
        if os.path.exists(protocols_path):
            try:
                with open(protocols_path, 'r') as f:
                    protocols_data = json.load(f)
                
                for protocol_id, protocol in protocols_data.items():
                    self.protocols[protocol_id] = NegotiatedProtocol(
                        id=protocol_id,
                        version=protocol.get("version", "1.0"),
                        description=protocol.get("description", ""),
                        schema=protocol.get("schema", {})
                    )
                
                logger.info(f"Loaded {len(self.protocols)} Agora protocols for {self.agent.did}")
            except Exception as e:
                logger.error(f"Error loading protocols: {e}")
    
    def _save_protocols(self) -> None:
        """Save protocols to disk"""
        protocols_path = self._get_protocols_path()
        
        protocols_data = {}
        for protocol_id, protocol in self.protocols.items():
            protocols_data[protocol_id] = {
                "version": protocol.version,
                "description": protocol.description,
                "schema": protocol.schema
            }
        
        try:
            with open(protocols_path, 'w') as f:
                json.dump(protocols_data, f, indent=2)
            
            logger.info(f"Saved {len(protocols_data)} Agora protocols for {self.agent.did}")
        except Exception as e:
            logger.error(f"Error saving protocols: {e}")
    
    async def send_message(self, message: Dict[str, Any], protocol_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to an Agora agent.
        
        Args:
            message: Message content to send
            protocol_id: Optional protocol ID to use
            
        Returns:
            Agent response
        """
        # Get protocol hash if a protocol ID is provided
        protocol_hash = None
        if protocol_id and protocol_id in self.protocols:
            protocol = self.protocols[protocol_id]
            protocol_hash = protocol.id
        
        # Prepare the payload
        payload = {
            "protocolHash": protocol_hash,
            "body": message
        }
        
        # Send message using Agora Protocol
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.post(
                    f"{self.agent.endpoint}/message",
                    json=payload
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to send message: {error_text}")
                
                result = await response.json()
                if result.get("status") != "success":
                    raise Exception(f"Failed to send message: {result.get('error')}")
                
                return result.get("body", {})
                
            except Exception as e:
                logger.error(f"Error communicating with Agora agent: {e}")
                raise
    
    async def negotiate_protocol(self, description: str) -> NegotiatedProtocol:
        """
        Negotiate a new protocol with an Agora agent.
        
        Args:
            description: Description of the protocol to negotiate
            
        Returns:
            The negotiated protocol
        """
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{self.agent.endpoint}/negotiate",
                    json={"description": description}
                )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to negotiate protocol: {error_text}")
                
                protocol_data = await response.json()
                
                # Create protocol object
                protocol = NegotiatedProtocol(
                    id=protocol_data.get("id"),
                    version=protocol_data.get("version", "1.0"),
                    description=description,
                    schema=protocol_data.get("schema", {})
                )
                
                # Store protocol
                self.protocols[protocol.id] = protocol
                self._save_protocols()
                
                logger.info(f"Successfully negotiated protocol: {protocol.id}")
                return protocol
                
        except Exception as e:
            logger.error(f"Error negotiating protocol with Agora agent: {e}")
            raise
    
    async def process_bridge_message(self, message: BridgeMessage) -> Any:
        """
        Process a bridge message from AT Protocol and translate it to Agora.
        
        Args:
            message: Bridge message to process
            
        Returns:
            Processing result
        """
        if message.target != "agora":
            raise ValueError("Message target must be agora")
        
        # Use protocol if specified
        if message.protocol and message.protocol.id in self.protocols:
            return await self.send_message(message.content, message.protocol.id)
        else:
            # Otherwise, use natural language
            return await self.send_message(message.content)
    
    async def process_social_content(self, content: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
        """
        Process social content with the Agora agent.
        
        Args:
            content: List of social content items (posts, profiles, etc.)
            task: Description of the processing task
            
        Returns:
            Processing results
        """
        # Try to use a specialized protocol if available
        protocol_id = None
        for pid, protocol in self.protocols.items():
            if "social content" in protocol.description.lower() or "content analysis" in protocol.description.lower():
                protocol_id = pid
                break
        
        # Create a message with the content and task
        message = {
            "content": content,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_message(message, protocol_id)
    
    async def create_summary(self, texts: List[str], max_length: int = 280) -> str:
        """
        Create a summary of multiple texts using the Agora agent.
        
        Args:
            texts: List of texts to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summary text
        """
        # Try to use a specialized protocol if available
        protocol_id = None
        for pid, protocol in self.protocols.items():
            if "summary" in protocol.description.lower() or "summarization" in protocol.description.lower():
                protocol_id = pid
                break
        
        # Create a message with the texts and parameters
        message = {
            "texts": texts,
            "max_length": max_length,
            "task": "summarize",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.send_message(message, protocol_id)
        return result.get("summary", "")
    
    def get_protocol(self, protocol_id: str) -> Optional[NegotiatedProtocol]:
        """
        Get a specific protocol by ID.
        
        Args:
            protocol_id: ID of the protocol to retrieve
            
        Returns:
            The protocol or None if not found
        """
        return self.protocols.get(protocol_id)
    
    def get_protocols(self) -> Dict[str, NegotiatedProtocol]:
        """
        Get all available protocols.
        
        Returns:
            Dictionary of protocol IDs to protocols
        """
        return self.protocols.copy()
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """
        Get statistics about negotiated protocols.
        
        Returns:
            Dictionary with protocol statistics
        """
        stats = {
            "total_protocols": len(self.protocols),
            "protocols": []
        }
        
        for protocol_id, protocol in self.protocols.items():
            proto_stats = {
                "id": protocol_id,
                "description": protocol.description,
                "version": protocol.version
            }
            
            if protocol.stats:
                proto_stats["compression_ratio"] = protocol.stats.get("compression_ratio")
                proto_stats["avg_processing_time"] = protocol.stats.get("avg_processing_time")
            
            stats["protocols"].append(proto_stats)
        
        return stats