"""
Base class for all CLI commands
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from rich.console import Console


class BaseCommand(ABC):
    """Base class for all CLI commands"""
    
    def __init__(self, console: Console):
        self.console = console
    
    @abstractmethod
    def get_name(self) -> str:
        """Return command name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return command description"""
        pass
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> None:
        """Execute the command"""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Return detailed help text"""
        pass
    
    def validate_args(self, args: List[str], required_count: int, max_count: int | None = None) -> None:
        """Validate command arguments"""
        if len(args) < required_count:
            raise ValueError(f"Command requires at least {required_count} argument(s)")
        if max_count is not None and len(args) > max_count:
            raise ValueError(f"Command accepts at most {max_count} argument(s)")
    
    def get_arg(self, args: List[str], index: int, default: Any = None) -> Any:
        """Get argument at specific index"""
        if index < len(args):
            return args[index]
        return default
    
    def format_help(self, usage: str, description: str, examples: List[str] | None = None) -> str:
        """Format help text"""
        help_text = f"Usage: {usage}\n\n{description}"
        
        if examples:
            help_text += "\n\nExamples:"
            for example in examples:
                help_text += f"\n  {example}"
        
        return help_text