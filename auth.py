"""
API Authentication module for API key management
"""

import os
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import hashlib
import secrets

# Security scheme
security = HTTPBearer(auto_error=False)

class APIKeyManager:
    """Manages API keys for authentication"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> set:
        """Load API keys from environment or create default"""
        # In production, load from database or secure storage
        default_key = os.getenv("API_KEY", "mk_default_key_for_testing")
        return {default_key}
    
    def _generate_default_key(self) -> str:
        """Generate a default API key"""
        return f"mk_{secrets.token_urlsafe(32)}"
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate if API key is valid"""
        return api_key in self.api_keys
    
    def add_api_key(self, api_key: str) -> None:
        """Add a new API key"""
        self.api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str) -> bool:
        """Remove an API key"""
        return self.api_keys.discard(api_key) is not None

# Global API key manager
api_key_manager = APIKeyManager()

def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to extract and validate API key"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    if not api_key_manager.validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

def get_optional_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Optional API key dependency for endpoints that work with or without auth"""
    if not credentials:
        return None
    
    api_key = credentials.credentials
    
    if not api_key_manager.validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key
