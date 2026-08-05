"""Paperclip Blueprints — generate deployable Paperclip company bundles from a Markdown brief."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

try:
    __version__ = _package_version("paperclip-blueprints")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0+unknown"
