"""Importing these modules registers their tools."""
from tools.registry import registry
from tools import system_tools, web_tools, memory_tools  # noqa: F401

__all__ = ["registry"]
