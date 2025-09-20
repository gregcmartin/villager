"""
Villager - An experimental technology project for AI agents and task scheduling.

This package provides AI agent scheduling, task management, RAG integration,
and various utility tools for automation and processing.
"""

__version__ = "0.2.1rc1"
__author__ = "stupidfish001"
__email__ = "shovel@hscsec.cn"
__description__ = "This was an experimental technology project"

# Import main components for easy access
try:
    from . import interfaces
    from . import scheduler
    from . import tools
    from . import test
except ImportError:
    # Handle cases where some modules might not be available
    pass

__all__ = [
    "interfaces",
    "scheduler", 
    "tools",
    "test",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]
