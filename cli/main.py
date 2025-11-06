#!/usr/bin/env python3
"""
RVC Server CLI Interface
Interactive command-line tool for testing ChatterVC server functionality
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .app import CLIApp
from .config import Config
from .exceptions import CLIError

console = Console()

def main():
    """Main entry point for the CLI application"""
    try:
        config = Config.load()
        app = CLIApp(config)
        asyncio.run(app.run())
    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()