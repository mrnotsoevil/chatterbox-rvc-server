# RVC Server CLI Interface

A comprehensive command-line interface for testing and interacting with the ChatterVC (Chatterbox + RVC) OpenAI-compatible TTS server.

## Features

- **Interactive CLI**: Easy-to-use command-line interface with rich terminal formatting
- **Connection Management**: Connect to and manage connections with the RVC server
- **Model & Voice Management**: List, set, and manage available TTS models and voices
- **Audio Synthesis**: Generate speech from text with real-time playback
- **Audio Export**: Export generated audio to various formats
- **Performance Benchmarking**: Run comprehensive performance benchmarks
- **State Management**: Persistent configuration and state management
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Installation

### Prerequisites

- Python 3.8 or higher
- Existing RVC server running (see main project README)

### Setup

1. **Install dependencies**:
   ```bash
   python setup_cli.py
   ```

2. **Or manually install**:
   ```bash
   pip install -r cli_requirements.txt
   ```

3. **Make CLI executable** (optional):
   ```bash
   chmod +x cli/main.py
   ```

4. **Global installation** (optional):
   ```bash
   sudo ln -sf $(pwd)/cli/main.py /usr/local/bin/rvc-cli
   ```

## Usage

### Starting the CLI

```bash
# Using Python
python cli/main.py

# If made executable
./cli/main.py

# If installed globally
rvc-cli
```

### Basic Commands

#### Help
```bash
help                    # Show all available commands
help connect            # Show help for specific command
```

#### Connection
```bash
connect                # Connect to localhost:7779
connect 192.168.1.100:7779  # Connect to specific server
connect localhost:8080  # Connect to custom port
```

#### Models & Voices
```bash
list-models            # List available TTS models
list-voices            # List available voice conversion models
set-model chatterbox   # Set current model
set-voice my_voice      # Set current voice
get-model               # Show current model
get-voice               # Show current voice
```

#### Audio Generation
```bash
say "Hello, world!"     # Generate and play speech
export output.wav      # Export last audio to file
```

#### Benchmarking
```bash
benchmark 5 "Test text" # Run benchmark with 5 iterations
```

### Interactive Usage

The CLI provides an interactive prompt with real-time status display:

```
● http://localhost:7779 | 🎤 my_voice | 📝 chatterbox > connect
✓ Connected to http://localhost:7779
✓ Loaded 2 models and 5 voices

● http://localhost:7779 | 🎤 my_voice | 📝 chatterbox > say "Hello, this is a test!"
✓ Audio generated and playing...
```

## Configuration

The CLI stores configuration in `~/.chattervc-cli/config.json`:

```json
{
  "server_url": "http://localhost:7779",
  "sample_rate": 24000,
  "audio_format": "wav",
  "volume": 1.0,
  "show_progress": true,
  "verbose_output": false
}
```

### Configuration Options

- `server_url`: RVC server URL (default: http://localhost:7779)
- `sample_rate`: Audio sample rate (default: 24000)
- `audio_format`: Audio format for export (default: wav)
- `volume`: Playback volume (default: 1.0)
- `show_progress`: Show progress indicators (default: true)
- `verbose_output`: Enable verbose output (default: false)

## Command Reference

### Connection Commands

#### `connect [ip:port]`
Establish connection to the RVC server.

**Arguments:**
- `ip:port` (optional): Server address and port (default: localhost:7779)

**Examples:**
```bash
connect
connect 192.168.1.100:7779
connect localhost:8080
```

### Model Commands

#### `list-models`
List all available TTS models from the server.

**Examples:**
```bash
list-models
```

#### `set-model <model_name>`
Set the current TTS model for synthesis.

**Arguments:**
- `model_name`: Model ID (chatterbox or chatterbox_rvc)

**Examples:**
```bash
set-model chatterbox
set-model chatterbox_rvc
```

#### `get-model`
Show the current model setting.

**Examples:**
```bash
get-model
```

### Voice Commands

#### `list-voices`
List all available voice conversion models.

**Examples:**
```bash
list-voices
```

#### `set-voice <voice_name>`
Set the current voice for synthesis.

**Arguments:**
- `voice_name`: Voice ID or name

**Examples:**
```bash
set-voice my_voice
set-voice voices/my_voice
set-voice random
```

#### `get-voice`
Show the current voice setting.

**Examples:**
```bash
get-voice
```

### Audio Commands

#### `say <text>`
Generate and play audio from text using current settings.

**Arguments:**
- `text`: Text to synthesize

**Examples:**
```bash
say "Hello, world!"
say "This is a test of the text-to-speech system."
```

#### `export <path>`
Export the last generated audio to a file.

**Arguments:**
- `path`: Output file path

**Examples:**
```bash
export output.wav
export /path/to/output.wav
export my_speech.flac
```

### Benchmark Commands

#### `benchmark <n> <text>`
Run performance benchmark with n iterations.

**Arguments:**
- `n`: Number of iterations
- `text`: Text to synthesize

**Examples:**
```bash
benchmark 5 "Hello world"
benchmark 10 "This is a longer text for benchmarking"
```

### Help Commands

#### `help [command]`
Show help information for all commands or a specific command.

**Arguments:**
- `command` (optional): Specific command name

**Examples:**
```bash
help
help say
help connect
```

## Architecture

The CLI is built with a modular architecture:

```
cli/
├── main.py              # Main entry point
├── app.py               # Core application class
├── config.py            # Configuration management
├── state.py             # State management
├── exceptions.py        # Custom exceptions
├── ui.py                # UI components
├── http_client.py       # HTTP client for server communication
├── audio_player.py      # Audio playback functionality
├── commands/            # Command implementations
│   ├── __init__.py
│   ├── base.py          # Base command class
│   ├── help.py
│   ├── connect.py
│   ├── list_models.py
│   ├── list_voices.py
│   ├── set_voice.py
│   ├── set_model.py
│   ├── get_voice.py
│   ├── get_model.py
│   ├── say.py
│   ├── export.py
│   └── benchmark.py
```

### Key Components

1. **CLIApp**: Main application class orchestrating all components
2. **Command System**: Extensible command architecture with base classes
3. **State Management**: Centralized state management for connection, models, voices, and audio
4. **HTTP Client**: Async HTTP client for server communication
5. **Audio Player**: Cross-platform audio playback functionality
6. **UI Components**: Rich terminal interface with progress indicators and status displays

## Error Handling

The CLI provides comprehensive error handling:

- **Connection Errors**: Clear error messages for connection failures
- **Validation Errors**: Input validation with helpful error messages
- **Audio Errors**: Graceful handling of audio playback issues
- **Configuration Errors**: Validation and recovery for configuration issues

## Audio Support

The CLI supports multiple audio formats:

- **WAV**: Uncompressed audio, highest quality
- **FLAC**: Lossless compression
- **OGG**: Vorbis compression, good balance

Audio playback is supported on:
- **Linux**: Uses aplay, paplay, or Python fallback
- **macOS**: Uses afplay or Python fallback
- **Windows**: Uses PowerShell or Python fallback

## Development

### Adding New Commands

1. Create a new command class inheriting from `BaseCommand`
2. Implement required methods: `get_name()`, `get_description()`, `execute()`, `get_help()`
3. Register the command in `CLIApp._register_commands()`

Example:
```python
class NewCommand(BaseCommand):
    def get_name(self) -> str:
        return "new-command"
    
    def get_description(self) -> str:
        return "Description of new command"
    
    async def execute(self, args: dict):
        # Command implementation
        pass
    
    def get_help(self) -> str:
        return self.format_help(
            usage="new-command [args]",
            description="Command description",
            examples=["new-command example"]
        )
```

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Connection Issues**: Check if RVC server is running and accessible
3. **Audio Issues**: Verify audio system permissions and dependencies
4. **Permission Errors**: Ensure proper file permissions for CLI execution

### Debug Mode

Enable verbose output for debugging:
```bash
# Edit config.json and set "verbose_output": true
# Or add environment variable
export CHATTERVC_VERBOSE=1
```

## License

This project is licensed under the MIT License - see the main project LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions:
- Check the main project documentation
- Review the troubleshooting section
- Create an issue in the project repository