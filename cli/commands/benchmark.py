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
                "benchmark speed",
                "benchmark quality"
            ]
        )
    
    async def execute(self, args: dict):
        args_list = args.get('args', [])
        
        try:
            test_type = args_list[0].lower() if args_list else "all"
            
            if test_type in ["all", "speed"]:
                await self._benchmark_speed()
            
            if test_type in ["all", "quality"]:
                await self._benchmark_quality()
                
            if test_type not in ["all", "speed", "quality"]:
                self.console.print(f"[red]Unknown benchmark type: {test_type}. Use 'speed', 'quality', or 'all'.[/red]")
                
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
    
    async def _benchmark_quality(self):
        """Benchmark audio quality"""
        self.console.print("Running quality benchmark...")
        
        test_texts = [
            "Short test.",
            "This is a medium length sentence for testing audio quality.",
            "This is a much longer sentence that should test the quality of the text-to-speech synthesis across different voice models and configurations."
        ]
        
        voice = self.state.voice.current_voice or "default"
        model = self.state.model.current_model or "default"
        
        quality_scores = []
        
        for i, text in enumerate(test_texts):
            try:
                self.console.print(f"[blue]Testing quality with text {i+1}/{len(test_texts)}...[/blue]")
                
                start_time = time.time()
                audio_data = await self.http_client.generate_speech(text, voice, model)
                end_time = time.time()
                
                if audio_data:
                    # Simple quality assessment based on response time and data size
                    response_time = end_time - start_time
                    data_size = len(audio_data) if audio_data else 0
                    
                    # Calculate a simple quality score (this is a placeholder)
                    quality_score = min(100, max(0, 100 - (response_time * 10) + (data_size / 1000)))
                    quality_scores.append(quality_score)
                    
                    self.console.print(f"  Response time: {response_time:.3f}s")
                    self.console.print(f"  Data size: {data_size} bytes")
                    self.console.print(f"  Estimated quality score: {quality_score:.1f}/100")
                else:
                    self.console.print(f"[yellow]No audio data returned for test {i+1}[/yellow]")
                    
            except Exception as e:
                self.console.print(f"[yellow]Quality test {i+1} failed: {e}[/yellow]")
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            self.console.print(f"[green]Quality Benchmark Results:[/green]")
            self.console.print(f"  Average quality score: {avg_quality:.1f}/100")
            self.console.print(f"  Tests completed: {len(quality_scores)}/{len(test_texts)}")
        else:
            self.console.print("[red]No successful quality tests completed.[/red]")