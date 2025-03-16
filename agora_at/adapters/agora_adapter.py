"""
Adapter for Agora Protocol integration with AT Protocol
"""

import requests
from typing import Dict, Any, List, Optional
from ..core.models import Agent, NegotiatedProtocol, BridgeMessage


class AgoraAdapter:
    """
    Adapter for Agora Protocol agent communication.
    """
    
    def __init__(self, agent: Agent):
        """
        Initialize the Agora Protocol adapter.
        
        Args:
            agent: Agent identity information
        """
        self.agent = agent
        self.protocols = {}  # Maps protocol IDs to protocol objects
    
    def send_message(self, message: Dict[str, Any], protocol_id: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Send message using Agora Protocol
        try:
            response = requests.post(
                f"{self.agent.endpoint}/message",
                json={
                    "protocolHash": protocol_hash,
                    "body": message
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to send message: {response.text}")
            
            result = response.json()
            if result.get("status") != "success":
                raise Exception(f"Failed to send message: {result.get('error')}")
            
            return result.get("body", {})
            
        except Exception as e:
            raise Exception(f"Error communicating with Agora agent: {str(e)}")
    
    def negotiate_protocol(self, description: str) -> NegotiatedProtocol:
        """
        Negotiate a new protocol with an Agora agent.
        
        Args:
            description: Description of the protocol to negotiate
            
        Returns:
            The negotiated protocol
        """
        try:
            response = requests.post(
                f"{self.agent.endpoint}/negotiate",
                json={"description": description}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to negotiate protocol: {response.text}")
            
            protocol_data = response.json()
            
            # Create protocol object
            protocol = NegotiatedProtocol(
                id=protocol_data.get("id"),
                version=protocol_data.get("version", "1.0"),
                description=description,
                schema=protocol_data.get("schema", {})
            )
            
            # Store protocol
            self.protocols[protocol.id] = protocol
            
            return protocol
            
        except Exception as e:
            raise Exception(f"Error negotiating protocol with Agora agent: {str(e)}")
    
    def process_bridge_message(self, message: BridgeMessage) -> Any:
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
            return self.send_message(message.content, message.protocol.id)
        else:
            # Otherwise, use natural language
            return self.send_message(message.content)
    
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
