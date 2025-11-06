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
            # Check if we have voices in state, if not fetch from server
            if not self.state.voice.available_voices:
                self.console.print("[yellow]Loading voices from server...[/yellow]")
                voices_response = await self.http_client.get_voices()
                
                # Update state with fresh voices
                models = self.state.model.available_models or {}  # Keep existing models
                self.state.update_server_info(models, voices_response)
            
            # Get voices from state
            available_voices = self.state.voice.available_voices
            
            if not available_voices:
                self.console.print("[yellow]No voices found.[/yellow]")
                return
            
            self.console.print("Available Voices:")
            for voice_id, voice_name in available_voices.items():
                # Try to get more detailed info if available
                voice_info = None
                try:
                    voices_response = await self.http_client.get_voices()
                    if isinstance(voices_response, dict) and 'voices' in voices_response:
                        for voice in voices_response['voices']:
                            if voice.get('id') == voice_id:
                                voice_info = voice
                                break
                except:
                    pass  # Ignore errors when getting detailed info
                
                if voice_info:
                    description = voice_info.get('description', 'No description')
                    available = voice_info.get('available', True)
                else:
                    description = 'No description'
                    available = True
                
                status = "[green]✓[/green]" if available else "[red]✗[/red]"
                current_marker = " [cyan](current)[/cyan]" if voice_id == self.state.voice.current_voice else ""
                self.console.print(f"  {status} {voice_name} [dim]({voice_id}){current_marker}[/dim] - {description}")
                
        except CLIError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to list voices: {e}[/red]")