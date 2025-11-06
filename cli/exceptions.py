"""
Custom exceptions for the RVC CLI Interface
"""


class CLIError(Exception):
    """Base exception for CLI errors"""
    pass


class ConnectionError(CLIError):
    """Connection related errors"""
    pass


class AudioError(CLIError):
    """Audio related errors"""
    pass


class ConfigurationError(CLIError):
    """Configuration related errors"""
    pass


class CommandError(CLIError):
    """Command execution errors"""
    pass


class ValidationError(CLIError):
    """Input validation errors"""
    pass


class FileNotFoundError(CLIError):
    """File not found errors"""
    pass