"""
Connect command implementation
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from .base import BaseCommand
from ..http_client import HTTPClient
from ..state import AppState
from ..exceptions import CLIError
from rich.console import Console


class ConnectCommand(BaseCommand):
    """Connect to the RVC server"""
    
    def __init__(self, console: Console, http_client: HTTPClient, state: AppState):
        super().__init__(console)
        self.http_client = http_client
        self.state = state
    
    def get_name(self) -> str:
        return "connect"
    
    def get_description(self) -> str:
        return "Establish connection to server"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="connect [ip:port]",
            description="Connect to the RVC server.",
            examples=[
                "connect",
                "connect 192.168.1.100:7779",
                "connect localhost:8080"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        # Parse connection string
        if args_list:
            connection_string = args_list[0]
            if ':' not in connection_string:
                raise CLIError(f"Invalid connection format: {connection_string}")
            server_url = f"http://{connection_string}"
        else:
            server_url = "http://localhost:7779"
        
        # Update state
        self.state.connection.server_url = server_url
        self.state.connection.connected = False
        self.state.connection.error_message = None
        
        # Test connection
        self.console.print(f"[yellow]Connecting to {server_url}...[/yellow]")
        
        try:
            await self.http_client.health_check()
            
            self.state.connection.connected = True
            self.state.connection.last_check = datetime.now()
            self.console.print(f"[green]✓ Connected to {server_url}[/green]")
            
            # Load available models and voices
            await self._load_server_info()
            
        except Exception as e:
            self.state.connection.connected = False
            self.state.connection.error_message = str(e)
            raise CLIError(f"Failed to connect: {e}")
    
    async def _load_server_info(self):
        """Load models and voices from server"""
        try:
            # Load models
            models_response = await self.http_client.get_models()
            models = {
                model['id']: model.get('name', model['id']) 
                for model in models_response.get('models', [])
            }
            
            # Load voices
            voices_response = await self.http_client.get_voices()
            voices = {
                voice['id']: voice.get('name', voice['id']) 
                for voice in voices_response.get('voices', [])
            }
            
            # Update state
            self.state.update_server_info(models, voices)
            
            self.console.print(f"[green]✓ Loaded {len(models)} models and {len(voices)} voices[/green]")
            
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not load server info: {e}[/yellow]")