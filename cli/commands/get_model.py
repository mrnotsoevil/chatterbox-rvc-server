"""
Get model command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class GetModelCommand(BaseCommand):
    """Get the current model"""
    
    def __init__(self, console: Console, state : AppState):
        super().__init__(console)
        self.state = state
    
    def get_name(self) -> str:
        return "get-model"
    
    def get_description(self) -> str:
        return "Get the current model"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="get-model",
            description="Get the currently selected model.",
            examples=[
                "get-model"
            ]
        )
    
    async def execute(self, args: dict):
        try:
            current_model = self.state.model.current_model
            if current_model:
                self.console.print(f"Current model: {current_model}")
            else:
                self.console.print("[yellow]No model selected.[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Failed to get model: {e}[/red]")