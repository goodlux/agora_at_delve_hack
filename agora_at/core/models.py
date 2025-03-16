"""
Core models for the Agora-AT Integration.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class AgentCapability(str, Enum):
    """Capabilities that an agent may have in the system."""
    READ_PUBLIC = "read:public"
    WRITE_POSTS = "write:posts"
    GENERATE_FEEDS = "generate:feeds"
    MODERATE_CONTENT = "moderate:content"
    INTERACT_USERS = "interact:users"


class Agent(BaseModel):
    """Representation of an agent in the integrated system."""
    did: str
    handle: Optional[str] = None
    capabilities: List[AgentCapability]
    endpoint: str
    description: str
    creator: Optional[str] = None


class NegotiatedProtocol(BaseModel):
    """Describes a negotiated protocol between agents."""
    id: str
    version: str
    description: str
    schema: Any
    stats: Optional[Dict[str, float]] = None


class ProtocolStats(BaseModel):
    """Statistics for a negotiated protocol."""
    compression_ratio: float = Field(0.0, alias="compressionRatio")
    avg_processing_time: float = Field(0.0, alias="avgProcessingTime")


class AgentPermission(BaseModel):
    """Permission granted by a user to an agent."""
    user_did: str = Field(..., alias="userDid")
    agent_did: str = Field(..., alias="agentDid")
    capability: AgentCapability
    granted_at: datetime = Field(default_factory=datetime.utcnow, alias="grantedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    limitations: Optional[Dict[str, Any]] = None


class FeedGeneratorConfig(BaseModel):
    """Configuration for agent-powered feed generation."""
    name: str
    description: str
    agent_did: str = Field(..., alias="agentDid")
    algorithm: str
    parameters: Optional[Dict[str, Any]] = None


class BridgeMessage(BaseModel):
    """Message exchanged between Agora and AT Protocol systems."""
    source: str = Field(..., regex="^(agora|atproto)$")
    target: str = Field(..., regex="^(agora|atproto)$")
    content: Any
    protocol: Optional[NegotiatedProtocol] = None
    meta: Optional[Dict[str, Any]] = None
