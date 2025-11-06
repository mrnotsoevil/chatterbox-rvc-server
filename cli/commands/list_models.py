"""
List models command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..http_client import HTTPClient
from ..state import AppState
from ..exceptions import CLIError
from rich.console import Console


class ListModelsCommand(BaseCommand):
    """List available TTS models"""
    
    def __init__(self, console: Console, http_client: HTTPClient, state: AppState):
        super().__init__(console)
        self.http_client = http_client
        self.state = state
    
    def get_name(self) -> str:
        return "list-models"
    
    def get_description(self) -> str:
        return "List available TTS models"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="list-models",
            description="List all available TTS models from the server.",
            examples=[
                "list-models"
            ]
        )
    
    async def execute(self, args: dict):
        if not self.state.connection.connected:
            raise CLIError("Not connected to server. Use 'connect' first.")
        
        try:
            models_response = await self.http_client.get_models()
            
            from rich.table import Table
            table = Table(title="Available TTS Models")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            
            for model in models_response.get('models', []):
                table.add_row(
                    model['id'],
                    model.get('name', model['id'])
                )
            
            self.console.print(table)
            
        except Exception as e:
            raise CLIError(f"Failed to list models: {e}")