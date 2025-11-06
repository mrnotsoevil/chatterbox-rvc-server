"""
Set model command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState


class SetModelCommand(BaseCommand):
    """Set the current model"""
    
    def __init__(self, console: Console, state : AppState):
        super().__init__(console)
        self.state = state
    
    def get_name(self) -> str:
        return "set-model"
    
    def get_description(self) -> str:
        return "Set the current model"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="set-model <model_name>",
            description="Set the current model for subsequent operations.",
            examples=[
                "set-model my_model",
                "set-model default"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        try:
            self.validate_args(args_list, 1, 1)
            model_name = args_list[0]
            
            # Set the model in state
            self.state.set_model(model_name)
            self.console.print(f"[green]Model set to: {model_name}[/green]")
            
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to set model: {e}[/red]")