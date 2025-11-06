"""
Help command implementation
"""

from typing import Dict, Any
from rich.console import Console
from .base import BaseCommand
from ..exceptions import CLIError


class HelpCommand(BaseCommand):
    """Show help information"""
    
    def __init__(self, console: Console, app):
        super().__init__(console)
        self.app = app
    
    def get_name(self) -> str:
        return "help"
    
    def get_description(self) -> str:
        return "Show available commands and usage"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="help [command]",
            description="Show help information for all commands or a specific command.",
            examples=[
                "help",
                "help say",
                "help connect"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        if args_list:
            # Show help for specific command
            command_name = args_list[0]
            success = self.app.command_registry.get_command_help(command_name, self.console)
            if not success:
                self.console.print(f"[red]Unknown command: {command_name}[/red]")
        else:
            # Show help for all commands
            self.app.ui.show_help_header()
            self.app.command_registry.show_help(self.console)