"""
User interface components
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from .state import AppState


class UIComponents:
    """User interface components"""
    
    def __init__(self, console: Console, state: AppState):
        self.console = console
        self.state = state
    
    def show_welcome(self):
        """Show welcome screen"""
        welcome_text = Text()
        welcome_text.append("RVC Server CLI Interface\n", style="bold blue")
        welcome_text.append("Interactive tool for testing ChatterVC server\n", style="green")
        welcome_text.append("Type 'help' for available commands\n", style="yellow")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    def get_prompt(self) -> str:
        """Get command prompt with current status"""
        status = self.state.get_status_summary()
        
        # Build status indicator
        status_parts = []
        if status['connected']:
            status_parts.append(f"[green]●[/green] {status['server_url']}")
        else:
            status_parts.append(f"[red]●[/red] disconnected")
        
        if status['current_voice']:
            status_parts.append(f"[cyan]🎤[/cyan] {status['current_voice']}")
        
        if status['current_model']:
            status_parts.append(f"[yellow]📝[/yellow] {status['current_model']}")
        
        status_str = " | ".join(status_parts)
        return f"{status_str} > "
    
    def show_progress(self, message: str):
        """Show progress indicator"""
        self.console.print(f"[yellow]{message}...[/yellow]")
    
    def show_error(self, message: str):
        """Show error message"""
        self.console.print(f"[red]Error: {message}[/red]")
    
    def show_success(self, message: str):
        """Show success message"""
        self.console.print(f"[green]✓ {message}[/green]")
    
    def show_warning(self, message: str):
        """Show warning message"""
        self.console.print(f"[yellow]! {message}[/yellow]")
    
    def show_info(self, message: str):
        """Show info message"""
        self.console.print(f"[blue]ℹ {message}[/blue]")
    
    def show_table(self, title: str, data: list, columns: list):
        """Show a table with data"""
        table = Table(title=title)
        
        # Add columns
        for col in columns:
            table.add_column(col, style="cyan")
        
        # Add rows
        for row in data:
            table.add_row(*row)
        
        self.console.print(table)
    
    def show_status_summary(self):
        """Show current status summary"""
        status = self.state.get_status_summary()
        
        table = Table(title="Current Status")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Server", status['server_url'] if status['connected'] else "Not connected")
        table.add_row("Connection", "Connected" if status['connected'] else "Disconnected")
        table.add_row("Current Voice", status['current_voice'] or "Not set")
        table.add_row("Current Model", status['current_model'] or "Not set")
        table.add_row("Sample Rate", str(status['sample_rate']))
        table.add_row("Audio Format", status['format'])
        table.add_row("Last Audio", "Available" if status['has_audio_data'] else "None")
        
        self.console.print(table)
    
    def show_help_header(self):
        """Show help header"""
        self.console.print(Panel(
            "RVC CLI Help\n"
            "Type 'help [command]' for specific command help",
            title="Help",
            border_style="blue"
        ))
    
    def show_command_help(self, command_name: str, description: str, help_text: str):
        """Show help for a specific command"""
        help_content = f"{command_name}\n\n"
        help_content += f"[green]{description}[/green]\n\n"
        help_content += f"[yellow]{help_text}[/yellow]"
        
        self.console.print(Panel(help_content, title=f"Help: {command_name}", border_style="green"))
    
    def show_benchmark_results(self, iterations: int, times: list):
        """Show benchmark results"""
        import statistics
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        table = Table(title="Benchmark Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Iterations", str(iterations))
        table.add_row("Average Time", f"{avg_time:.3f}s")
        table.add_row("Min Time", f"{min_time:.3f}s")
        table.add_row("Max Time", f"{max_time:.3f}s")
        table.add_row("Median Time", f"{median_time:.3f}s")
        table.add_row("Total Time", f"{sum(times):.3f}s")
        
        self.console.print(table)
    
    def show_loading_spinner(self, message: str):
        """Show loading spinner"""
        from rich.spinner import Spinner
        from rich.live import Live
        
        spinner = Spinner("dots", text=f"[yellow]{message}...[/yellow]")
        return Live(spinner, refresh_per_second=10)
    
    def clear_screen(self):
        """Clear the terminal screen"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')