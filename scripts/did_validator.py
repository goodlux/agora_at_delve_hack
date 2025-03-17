#!/usr/bin/env python3
"""
DID Validator for AT Protocol

This script loads and validates DID configurations for AT Protocol agents.
It can be used to verify that your DIDs are properly configured and accessible.
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64
from urllib.parse import urlparse

class DIDValidator:
    """Load and validate DID configurations for AT Protocol agents"""
    
    def __init__(self, config_dir: str = "./generated_dids"):
        """
        Initialize the DID validator.
        
        Args:
            config_dir (str): Directory containing agent configuration files
        """
        self.config_dir = Path(config_dir)
        self.agent_configs = {}
        
    def load_agent_configs(self) -> Dict[str, Dict]:
        """
        Load all agent configuration files from the config directory.
        
        Returns:
            Dict[str, Dict]: Dictionary of agent configurations indexed by agent name
        """
        self.agent_configs = {}
        
        # Find all config files
        config_files = list(self.config_dir.glob("*_config.json"))
        
        if not config_files:
            print(f"No configuration files found in {self.config_dir}")
            return self.agent_configs
        
        # Load each config file
        for config_path in config_files:
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    agent_name = config.get('name', '').lower()
                    if agent_name:
                        self.agent_configs[agent_name] = config
                        print(f"Loaded configuration for agent: {agent_name}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {config_path}: {e}")
        
        return self.agent_configs
    
    def _parse_did_web(self, did: str) -> Optional[str]:
        """
        Parse a did:web identifier and return the domain.
        
        Args:
            did (str): A DID in the format did:web:domain
            
        Returns:
            Optional[str]: The domain part of the DID or None if invalid
        """
        if not did.startswith("did:web:"):
            return None
        
        domain = did[8:]  # Remove 'did:web:' prefix
        return domain
    
    def validate_local_config(self, agent_name: str) -> Tuple[bool, List[str]]:
        """
        Validate a local agent configuration for consistency.
        
        Args:
            agent_name (str): Name of the agent to validate
            
        Returns:
            Tuple[bool, List[str]]: (validation success, list of validation messages)
        """
        messages = []
        is_valid = True
        
        # Check if agent exists in configs
        if agent_name not in self.agent_configs:
            return False, [f"Agent '{agent_name}' not found in loaded configurations"]
        
        config = self.agent_configs[agent_name]
        
        # Check required fields
        required_fields = ['name', 'did', 'handle', 'privateKey', 'publicKey']
        for field in required_fields:
            if field not in config:
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        if not is_valid:
            return is_valid, messages
        
        # Validate DID format
        if not config['did'].startswith('did:web:'):
            messages.append(f"Invalid DID format: {config['did']}. Expected did:web:domain")
            is_valid = False
        
        # Validate handle
        domain = self._parse_did_web(config['did'])
        if domain and domain != config['handle']:
            messages.append(f"Handle mismatch: DID domain is {domain} but handle is {config['handle']}")
            is_valid = False
        
        # Validate public key format
        if 'publicKey' in config:
            if not isinstance(config['publicKey'], dict):
                messages.append("Invalid publicKey format: expected a dictionary")
                is_valid = False
            elif 'x' not in config['publicKey'] or 'y' not in config['publicKey']:
                messages.append("Invalid publicKey format: missing x or y components")
                is_valid = False
        
        if is_valid:
            messages.append(f"Local configuration for agent '{agent_name}' is valid")
        
        return is_valid, messages
    
    def validate_remote_did(self, agent_name: str, use_https: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate a remote DID document by fetching it from the web.
        
        Args:
            agent_name (str): Name of the agent to validate
            use_https (bool): Whether to use HTTPS or HTTP for validation
            
        Returns:
            Tuple[bool, List[str]]: (validation success, list of validation messages)
        """
        messages = []
        is_valid = True
        
        # Check if agent exists in configs
        if agent_name not in self.agent_configs:
            return False, [f"Agent '{agent_name}' not found in loaded configurations"]
        
        config = self.agent_configs[agent_name]
        domain = self._parse_did_web(config['did'])
        
        if not domain:
            return False, [f"Invalid DID format: {config['did']}"]
        
        # Try to fetch the DID document
        protocol = "https" if use_https else "http"
        did_url = f"{protocol}://{domain}/.well-known/did.json"
        
        try:
            response = requests.get(did_url, timeout=10)
            if response.status_code != 200:
                messages.append(f"Failed to fetch DID document from {did_url}: {response.status_code}")
                is_valid = False
            else:
                try:
                    did_doc = response.json()
                    
                    # Basic validation of the DID document
                    if 'id' not in did_doc:
                        messages.append("Invalid DID document: missing 'id' field")
                        is_valid = False
                    elif did_doc['id'] != config['did']:
                        messages.append(f"DID mismatch: document has {did_doc['id']} but config has {config['did']}")
                        is_valid = False
                    
                    # Verify public key matches
                    if 'verificationMethod' not in did_doc or not did_doc['verificationMethod']:
                        messages.append("Invalid DID document: missing or empty 'verificationMethod'")
                        is_valid = False
                    else:
                        # Find the key in the verification methods
                        found_key = False
                        for method in did_doc['verificationMethod']:
                            if 'publicKeyJwk' in method:
                                jwk = method['publicKeyJwk']
                                if jwk.get('x') == config['publicKey'].get('x') and jwk.get('y') == config['publicKey'].get('y'):
                                    found_key = True
                                    break
                        
                        if not found_key:
                            messages.append("Public key in configuration does not match any key in the DID document")
                            is_valid = False
                    
                    if is_valid:
                        messages.append(f"Remote DID document for agent '{agent_name}' is valid and matches configuration")
                    
                except json.JSONDecodeError:
                    messages.append(f"Invalid JSON in DID document at {did_url}")
                    is_valid = False
        
        except requests.RequestException as e:
            messages.append(f"Error fetching DID document from {did_url}: {e}")
            is_valid = False
        
        return is_valid, messages
    
    def validate_all_agents(self, use_https: bool = True) -> Dict[str, Dict]:
        """
        Validate all loaded agent configurations, both locally and remotely.
        
        Args:
            use_https (bool): Whether to use HTTPS or HTTP for remote validation
            
        Returns:
            Dict[str, Dict]: Results of validation for each agent
        """
        results = {}
        
        # Load configs if not already loaded
        if not self.agent_configs:
            self.load_agent_configs()
        
        # Validate each agent
        for agent_name in self.agent_configs:
            local_valid, local_messages = self.validate_local_config(agent_name)
            remote_valid, remote_messages = self.validate_remote_did(agent_name, use_https)
            
            results[agent_name] = {
                'local': {
                    'valid': local_valid,
                    'messages': local_messages
                },
                'remote': {
                    'valid': remote_valid,
                    'messages': remote_messages
                },
                'overall_valid': local_valid and remote_valid
            }
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate DID configurations for AT Protocol agents")
    parser.add_argument("--config-dir", default="./generated_dids", help="Directory containing agent configuration files")
    parser.add_argument("--agent", help="Specific agent to validate (validates all if not specified)")
    parser.add_argument("--http", action="store_true", help="Use HTTP instead of HTTPS for remote validation")
    parser.add_argument("--local-only", action="store_true", help="Only perform local validation (no network requests)")
    
    args = parser.parse_args()
    
    validator = DIDValidator(args.config_dir)
    validator.load_agent_configs()
    
    use_https = not args.http
    
    if args.agent:
        # Validate specific agent
        print(f"Validating agent: {args.agent}")
        
        local_valid, local_messages = validator.validate_local_config(args.agent)
        print("\nLocal validation:", "✅ VALID" if local_valid else "❌ INVALID")
        for msg in local_messages:
            print(f"  {'✓' if local_valid else '✗'} {msg}")
        
        if not args.local_only:
            remote_valid, remote_messages = validator.validate_remote_did(args.agent, use_https)
            print("\nRemote validation:", "✅ VALID" if remote_valid else "❌ INVALID")
            for msg in remote_messages:
                print(f"  {'✓' if remote_valid else '✗'} {msg}")
        
        overall = local_valid and (remote_valid if not args.local_only else True)
        print("\nOverall validation:", "✅ VALID" if overall else "❌ INVALID")
    
    else:
        # Validate all agents
        print("Validating all agents...")
        
        if args.local_only:
            # Only local validation
            for agent_name in validator.agent_configs:
                local_valid, local_messages = validator.validate_local_config(agent_name)
                print(f"\nAgent: {agent_name} - {local_valid}")
                for msg in local_messages:
                    print(f"  {msg}")
        else:
            # Full validation
            results = validator.validate_all_agents(use_https)
            
            all_valid = True
            for agent_name, result in results.items():
                if not result['overall_valid']:
                    all_valid = False
                
                print(f"\nAgent: {agent_name}")
                print("  Local: ", "✅ VALID" if result['local']['valid'] else "❌ INVALID")
                for msg in result['local']['messages']:
                    print(f"    {msg}")
                
                print("  Remote:", "✅ VALID" if result['remote']['valid'] else "❌ INVALID")
                for msg in result['remote']['messages']:
                    print(f"    {msg}")
            
            print("\nOverall validation:", "✅ VALID" if all_valid else "❌ INVALID")


if __name__ == "__main__":
    main()