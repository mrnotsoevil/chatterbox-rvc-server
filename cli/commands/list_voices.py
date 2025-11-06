"""
List voices command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class ListVoicesCommand(BaseCommand):
    """List available voices"""
    
    def __init__(self, console: Console, http_client, state : AppState):
        super().__init__(console)
        self.http_client = http_client
        self.state = state
    
    def get_name(self) -> str:
        return "list-voices"
    
    def get_description(self) -> str:
        return "List all available voices"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="list-voices",
            description="List all available voices from the server.",
            examples=[
                "list-voices"
            ]
        )
    
    async def execute(self, args: dict):
        try:
            voices = await self.http_client.get_voices()
            print(voices)
            
            if not voices:
                self.console.print("[yellow]No voices found.[/yellow]")
                return
            
            self.console.print("Available Voices:")
            for voice in voices:
                status = "[green]✓[/green]" if voice.get("available", True) else "[red]✗[/red]"
                self.console.print(f"  {status} {voice.get('name', 'Unknown')} - {voice.get('description', 'No description')}")
                
        except CLIError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to list voices: {e}[/red]")