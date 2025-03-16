#!/usr/bin/env python3
"""
Example of a Multi-Agent Specialized Knowledge Network using Agora and AT Protocol

This demonstrates the concept of specialized agents (Alice, Bob, Charlie) where:
- Alice: Main coordinator that interfaces with the user
- Bob: Specialized for Internet Archive access
- Charlie: Specialized for Bluesky posting
"""

import requests
from typing import Dict, Any, List, Optional
import json
import os


class AgoraAgent:
    """Base class for Agora Protocol agents"""
    
    def __init__(self, name: str, endpoint: str):
        self.name = name
        self.endpoint = endpoint
        self.protocols = {}  # Store negotiated protocols
    
    def send_message(self, message: Dict[str, Any], protocol_hash: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to this agent using Agora Protocol"""
        payload = {
            "protocolHash": protocol_hash,
            "body": message
        }
        
        response = requests.post(f"{self.endpoint}/message", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to communicate with agent {self.name}: {response.text}")
        
        return response.json()
    
    def negotiate_protocol(self, description: str) -> str:
        """Negotiate a new protocol with this agent"""
        payload = {
            "description": description
        }
        
        response = requests.post(f"{self.endpoint}/negotiate", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to negotiate protocol with agent {self.name}: {response.text}")
        
        result = response.json()
        protocol_hash = result.get("protocolHash")
        self.protocols[description] = protocol_hash
        return protocol_hash


class ATProtoClient:
    """Basic client for interacting with AT Protocol"""
    
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.session = None
    
    def login(self, handle: str, password: str) -> Dict[str, Any]:
        """Login to AT Protocol service"""
        response = requests.post(
            f"{self.service_url}/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password}
        )
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        
        self.session = response.json()
        return self.session
    
    def create_post(self, text: str) -> Dict[str, Any]:
        """Create a post on the AT Protocol network"""
        if not self.session:
            raise Exception("Not logged in")
        
        response = requests.post(
            f"{self.service_url}/xrpc/com.atproto.repo.createRecord",
            headers={
                "Authorization": f"Bearer {self.session['accessJwt']}",
            },
            json={
                "repo": self.session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "text": text,
                    "createdAt": "2023-01-01T00:00:00.000Z",  # Would use current time in real implementation
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create post: {response.text}")
        
        return response.json()


class MultiAgentNetwork:
    """Demonstration of a multi-agent network with AT Protocol integration"""
    
    def __init__(self):
        # Initialize our agents
        self.alice = AgoraAgent("Alice", "https://alice-agent.example.com")
        self.bob = AgoraAgent("Bob", "https://bob-agent.example.com")
        self.charlie = AgoraAgent("Charlie", "https://charlie-agent.example.com")
        
        # Initialize AT Protocol client for Charlie
        self.atproto_client = ATProtoClient("https://bsky.social")
    
    def setup(self):
        """Set up the agent network with negotiated protocols"""
        print("Setting up agent network...")
        
        # Negotiate specialized protocols
        self.archive_protocol = self.bob.negotiate_protocol(
            "Efficient protocol for querying Internet Archive materials with filtered results"
        )
        
        self.posting_protocol = self.charlie.negotiate_protocol(
            "Protocol for creating and formatting social media posts with metadata"
        )
        
        print("Protocols negotiated successfully")
    
    def process_user_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent network"""
        print(f"User query: {query}")
        
        # Alice analyzes the query
        alice_response = self.alice.send_message({"query": query, "type": "user_request"})
        
        # If archive research is needed, Alice delegates to Bob
        if "archive_research" in alice_response.get("actions", []):
            print("Delegating to Bob for archive research...")
            archive_query = alice_response.get("archive_query", query)
            bob_response = self.bob.send_message(
                {"query": archive_query, "format": "comprehensive"},
                protocol_hash=self.archive_protocol
            )
            
            # Alice synthesizes Bob's response
            synthesis_response = self.alice.send_message({
                "type": "synthesis",
                "original_query": query,
                "archive_results": bob_response.get("results", [])
            })
            
            # If a post should be created, delegate to Charlie
            if synthesis_response.get("should_post", False):
                print("Delegating to Charlie for social posting...")
                post_content = synthesis_response.get("post_content", "")
                charlie_response = self.charlie.send_message(
                    {"content": post_content, "platform": "bluesky"},
                    protocol_hash=self.posting_protocol
                )
                
                # In a real implementation, Charlie would use the AT Protocol client
                # self.atproto_client.create_post(charlie_response.get("formatted_content", ""))
                
                synthesis_response["post_status"] = charlie_response.get("status")
            
            return synthesis_response
        
        return alice_response


# Example usage (would actually connect to real endpoints in production)
def run_example():
    print("Multi-Agent Specialized Knowledge Network")
    print("=========================================")
    
    network = MultiAgentNetwork()
    network.setup()
    
    # Simulate user query
    result = network.process_user_query(
        "Can you find information about the Apollo 11 mission from the Internet Archive and post a summary to Bluesky?"
    )
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    print("\nThis example demonstrates the concept of specialized agents using Agora Protocol")
    print("for efficient communication, with AT Protocol integration for social interaction.")


if __name__ == "__main__":
    run_example()
