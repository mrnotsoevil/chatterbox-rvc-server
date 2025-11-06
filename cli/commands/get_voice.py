"""
Get voice command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class GetVoiceCommand(BaseCommand):
    """Get the current voice"""
    
    def __init__(self, console: Console, state : AppState):
        super().__init__(console)
        self.state = state
    
    def get_name(self) -> str:
        return "get-voice"
    
    def get_description(self) -> str:
        return "Get the current voice"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="get-voice",
            description="Get the currently selected voice.",
            examples=[
                "get-voice"
            ]
        )
    
    async def execute(self, args: dict):
        try:
            current_voice = self.state.voice.current_voice
            if current_voice:
                self.console.print(f"Current voice: {current_voice}")
            else:
                self.console.print("[yellow]No voice selected.[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Failed to get voice: {e}[/red]")