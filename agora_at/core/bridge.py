"""
Protocol Bridge for connecting Agora Protocol and AT Protocol
"""

from typing import Dict, Any, Optional
from ..core.models import Agent, BridgeMessage, NegotiatedProtocol
from ..adapters.agora_adapter import AgoraAdapter
from ..adapters.atproto_adapter import ATProtoAdapter


class ProtocolBridge:
    """
    Bridge for translating between Agora Protocol and AT Protocol.
    """
    
    def __init__(self, agora_agent: Agent, atproto_agent: Agent, atproto_service_url: str):
        """
        Initialize the protocol bridge.
        
        Args:
            agora_agent: Agora agent identity
            atproto_agent: AT Protocol agent identity
            atproto_service_url: URL of the AT Protocol service
        """
        self.agora_adapter = AgoraAdapter(agora_agent)
        self.atproto_adapter = ATProtoAdapter(atproto_service_url, atproto_agent)
        
        # Mapping of message types to protocol handlers
        self.protocol_handlers = {}
    
    def register_protocol(self, message_type: str, protocol: NegotiatedProtocol) -> None:
        """
        Register a protocol for a specific message type.
        
        Args:
            message_type: Type of message
            protocol: Protocol to use for this message type
        """
        self.protocol_handlers[message_type] = protocol
    
    def send_to_agora(self, message: Dict[str, Any], message_type: Optional[str] = None) -> Dict[str, Any]:
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
            protocol=self.protocol_handlers.get(message_type) if message_type else None
        )
        
        # Process through adapter
        return self.agora_adapter.process_bridge_message(bridge_message)
    
    def send_to_atproto(self, message: Dict[str, Any], message_type: Optional[str] = None) -> Dict[str, Any]:
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
            protocol=self.protocol_handlers.get(message_type) if message_type else None
        )
        
        # Process through adapter
        return self.atproto_adapter.process_bridge_message(bridge_message)
    
    def negotiate_protocol(self, description: str) -> NegotiatedProtocol:
        """
        Negotiate a new protocol with an Agora agent.
        
        Args:
            description: Description of the protocol to negotiate
            
        Returns:
            The negotiated protocol
        """
        return self.agora_adapter.negotiate_protocol(description)
    
    def login_atproto(self, handle: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the AT Protocol service.
        
        Args:
            handle: User handle or identifier
            password: Authentication password or token
            
        Returns:
            Session information
        """
        return self.atproto_adapter.login(handle, password)
