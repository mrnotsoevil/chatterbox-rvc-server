"""
Say command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class SayCommand(BaseCommand):
    """Text-to-speech functionality"""
    
    def __init__(self, console: Console, http_client, audio_player, state : AppState):
        super().__init__(console)
        self.http_client = http_client
        self.audio_player = audio_player
        self.state = state
    
    def get_name(self) -> str:
        return "say"
    
    def get_description(self) -> str:
        return "Convert text to speech"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="say <text>",
            description="Convert text to speech using the current voice and model.",
            examples=[
                "say Hello, this is a test.",
                "say The weather is nice today."
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        try:
            self.validate_args(args_list, 1)
            text = ' '.join(args_list)
            
            # Get current voice and model from state
            voice = self.state.voice.current_voice
            model = self.state.model.current_model
            
            if not voice:
                self.console.print("[yellow]No voice selected. Using default.[/yellow]")
                voice = "default"
            
            if not model:
                self.console.print("[yellow]No model selected. Using default.[/yellow]")
                model = "chatterbox_rvc"
            
            self.console.print(f"[blue]Converting text to speech with voice: {voice}, model: {model}[/blue]")
            
            # Generate speech
            audio_data = await self.http_client.generate_speech(text, voice, model)
            
            if audio_data:
                # Play the audio
                self.console.print("[green]Playing audio...[/green]")
                await self.audio_player.play(audio_data)
                self.console.print("[green]Audio playback completed.[/green]")
            else:
                self.console.print("[red]Failed to generate audio.[/red]")
                
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except CLIError as e:
            self.console.print(f"[red]CLI Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to generate speech: {e}[/red]")