"""
Benchmark command implementation
"""

from typing import Dict, Any, TYPE_CHECKING
from .base import BaseCommand
from ..exceptions import CLIError
from rich.console import Console
from ..state import AppState
import time
import asyncio


class BenchmarkCommand(BaseCommand):
    """Run performance benchmarks"""
    
    def __init__(self, console : Console, http_client, state : AppState):
        super().__init__(console)
        self.http_client = http_client
        self.state = state
    
    def get_name(self) -> str:
        return "benchmark"
    
    def get_description(self) -> str:
        return "Run performance benchmarks"
    
    def get_help(self) -> str:
        return self.format_help(
            usage="benchmark [test_type]",
            description="Run performance benchmarks on the server.",
            examples=[
                "benchmark",
                "benchmark speed"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        try:
            test_type = args_list[0].lower() if args_list else "speed"
            
            if test_type in ["all", "speed"]:
                await self._benchmark_speed()
            else:
                self.console.print(f"[red]Unknown benchmark type: {test_type}. Use 'speed' or 'all'.[/red]")
                
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")
        except CLIError as e:
            self.console.print(f"[red]CLI Error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Failed to run benchmark: {e}[/red]")
    
    async def _benchmark_speed(self):
        """Benchmark server response speed"""
        self.console.print("Running speed benchmark...")
        
        test_text = "This is a test sentence for benchmarking."
        voice = self.state.voice.current_voice or "default"
        model = self.state.model.current_model or "default"
        
        # Get voice info for better display
        voice_info = self.state.get_voice_info()
        if voice_info['current_voice_name']:
            self.console.print(f"[blue]Running speed benchmark with voice: {voice_info['current_voice_name']} (ID: {voice}), model: {model}[/blue]")
        else:
            self.console.print(f"[blue]Running speed benchmark with voice: {voice}, model: {model}[/blue]")
        
        # Warm up
        try:
            await self.http_client.generate_speech("Warm up", voice, model)
        except:
            pass
        
        # Run multiple tests
        times = []
        for i in range(5):
            start_time = time.time()
            try:
                await self.http_client.generate_speech(test_text, voice, model)
                end_time = time.time()
                times.append(end_time - start_time)
            except Exception as e:
                self.console.print(f"[yellow]Speed test {i+1} failed: {e}[/yellow]")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            self.console.print(f"[green]Speed Benchmark Results:[/green]")
            self.console.print(f"  Average response time: {avg_time:.3f}s")
            self.console.print(f"  Minimum response time: {min_time:.3f}s")
            self.console.print(f"  Maximum response time: {max_time:.3f}s")
            self.console.print(f"  Total tests completed: {len(times)}/5")
        else:
            self.console.print("[red]No successful speed tests completed.[/red]")
    