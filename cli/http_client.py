"""
HTTP client for server communication
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from .exceptions import ConnectionError, CLIError


class HTTPClient:
    """HTTP client for server communication"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        if not self.session:
            raise CLIError("HTTP client not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    raise ConnectionError(f"Health check failed: {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {e}")
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models"""
        if not self.session:
            raise CLIError("HTTP client not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/v1/audio/models") as response:
                if response.status != 200:
                    raise CLIError(f"Failed to get models: {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to get models: {e}")
    
    async def get_voices(self) -> Dict[str, Any]:
        """Get available voices"""
        if not self.session:
            raise CLIError("HTTP client not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/v1/audio/voices") as response:
                if response.status != 200:
                    raise CLIError(f"Failed to get voices: {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to get voices: {e}")
    
    async def speech_synthesis(self, request_data: Dict[str, Any]) -> aiohttp.ClientResponse:
        """Generate speech"""
        if not self.session:
            raise CLIError("HTTP client not initialized")
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/audio/speech",
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise CLIError(f"Speech synthesis failed: {response.status} - {error_text}")
                return response
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Speech synthesis failed: {e}")
    
    async def get_root_info(self) -> Dict[str, Any]:
        """Get root server information"""
        if not self.session:
            raise CLIError("HTTP client not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status != 200:
                    raise CLIError(f"Failed to get server info: {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to get server info: {e}")