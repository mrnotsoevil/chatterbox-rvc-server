"""
Command system for the RVC CLI Interface
"""

from typing import Dict, List, Optional
from .base import BaseCommand


class CommandRegistry:
    """Registry for managing CLI commands"""
    
    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}
        self.aliases: Dict[str, str] = {}
    
    def register(self, command: BaseCommand):
        """Register a command"""
        name = command.get_name()
        self.commands[name] = command
        
        # Register aliases
        aliases = getattr(command, 'aliases', [])
        for alias in aliases:
            self.aliases[alias] = name
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get command by name or alias"""
        # Check if it's an alias
        if name in self.aliases:
            name = self.aliases[name]
        
        return self.commands.get(name)
    
    def list_commands(self) -> List[str]:
        """List all available command names"""
        return list(self.commands.keys())
    
    def show_help(self, console):
        """Show help for all commands"""
        from rich.table import Table
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        
        for name, command in self.commands.items():
            table.add_row(name, command.get_description())
        
        console.print(table)
    
    def get_command_help(self, command_name: str, console) -> bool:
        """Get help for a specific command"""
        command = self.get_command(command_name)
        if command:
            console.print(command.get_help())
            return True
        return False