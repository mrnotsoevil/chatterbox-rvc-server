"""
Core application class for the RVC CLI Interface
"""

import asyncio
from typing import Dict, Optional
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from .config import Config
from .commands import CommandRegistry
from .state import AppState
from .http_client import HTTPClient
from .audio_player import AudioPlayer
from .ui import UIComponents
from .exceptions import CLIError


class CLIApp:
    """Main CLI application class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        self.state = AppState()
        self.http_client = HTTPClient(config.server_url)
        self.audio_player = AudioPlayer()
        self.command_registry = CommandRegistry()
        self.ui = UIComponents(self.console, self.state)
        
        # Register commands
        self._register_commands()
    
    def _register_commands(self):
        """Register all available commands"""
        from .commands.help import HelpCommand
        from .commands.connect import ConnectCommand
        from .commands.list_models import ListModelsCommand
        from .commands.list_voices import ListVoicesCommand
        from .commands.set_voice import SetVoiceCommand
        from .commands.set_model import SetModelCommand
        from .commands.get_voice import GetVoiceCommand
        from .commands.get_model import GetModelCommand
        from .commands.say import SayCommand
        from .commands.benchmark import BenchmarkCommand
        
        commands = [
            HelpCommand(self.console, self),
            ConnectCommand(self.console, self.http_client, self.state),
            ListModelsCommand(self.console, self.http_client, self.state),
            ListVoicesCommand(self.console, self.http_client, self.state),
            SetVoiceCommand(self.console, self.state, self.http_client),
            SetModelCommand(self.console, self.state),
            GetVoiceCommand(self.console, self.state),
            GetModelCommand(self.console, self.state),
            SayCommand(self.console, self.http_client, self.audio_player, self.state),
            BenchmarkCommand(self.console, self.http_client, self.state),
        ]
        
        for cmd in commands:
            self.command_registry.register(cmd)
    
    async def run(self):
        """Run the CLI application"""
        # Initialize HTTP client session
        async with self.http_client:
            # Show welcome screen
            self.ui.show_welcome()
            
            # Main command loop
            while True:
                try:
                    # Show prompt with current status
                    prompt_text = self.ui.get_prompt()
                    command_input = await self._get_user_input(prompt_text)
                    
                    if not command_input:
                        continue
                    
                    # Parse and execute command
                    await self._execute_command(command_input)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
    
    async def _get_user_input(self, prompt_text: str) -> str:
        """Get user input with proper prompt formatting"""
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: input(f"\n{prompt_text}")
        )
    
    async def _execute_command(self, command_input: str):
        """Parse and execute a command"""
        parts = command_input.strip().split()
        if not parts:
            return
        
        command_name = parts[0]
        args = parts[1:]
        
        command = self.command_registry.get_command(command_name)
        if command:
            await command.execute({"args": args})
        else:
            self.console.print(f"[red]Unknown command: {command_name}[/red]")
            self.command_registry.show_help(self.console)