"""
Set voice command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class SetVoiceCommand(BaseCommand):
    """Set the current voice"""
    
    def __init__(self, console: Console, state: AppState, http_client=None):
        super().__init__(console)
        self.state = state
        self.http_client = http_client
    
    def get_name(self) -> str:
        return "set-voice"
    
    def get_description(self) -> str:
        return "Set the current voice"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="set-voice <voice_name>",
            description="Set the current voice for subsequent operations.",
            examples=[
                "set-voice my_voice",
                "set-voice default"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        try:
            self.validate_args(args_list, 1, 1)
            voice_input = args_list[0]
            
            # Set the voice in state (with automatic voice fetching)
            await self.state.set_voice(voice_input, self.http_client)
            
            # Get voice info for better feedback
            voice_info = self.state.get_voice_info()
            self.console.print(f"[green]Voice set to: {voice_info['current_voice_name']} (ID: {voice_info['current_voice']})[/green]")
            
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to set voice: {e}[/red]")