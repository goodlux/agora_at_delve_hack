#!/usr/bin/env python3
"""
Test DID Configuration for AT Protocol Agents
"""
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the DID validator
from scripts.did_validator import DIDValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Set secure key path
    secure_key_path = os.environ.get(
        'ATPROTO_KEY_PATH', 
        os.path.expanduser('~/secure_location/agora_at_keys')
    )
    
    print(f"Using secure key path: {secure_key_path}")
    
    # Create validator
    validator = DIDValidator(secure_key_path)
    
    # Load agent configs
    agent_configs = validator.load_agent_configs()
    agents = list(agent_configs.keys())
    print(f"Available agents: {', '.join(agents)}")
    
    # Validate all agents
    for agent in agents:
        print(f"\nValidating {agent}...")
        local_valid, local_messages = validator.validate_local_config(agent)
        print(f"Local validation: {'✓ PASS' if local_valid else '✗ FAIL'}")
        for msg in local_messages:
            print(f"  - {msg}")
        
        remote_valid, remote_messages = validator.validate_remote_did(agent, use_https=False)
        print(f"Remote validation: {'✓ PASS' if remote_valid else '✗ FAIL'}")
        for msg in remote_messages:
            print(f"  - {msg}")

if __name__ == "__main__":
    main()