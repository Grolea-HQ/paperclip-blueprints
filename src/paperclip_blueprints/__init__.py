"""Paperclip Blueprints — generate deployable Paperclip company bundles from a Markdown brief."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

#: What ``__version__`` resolves to when the package metadata is absent. Named rather than
#: repeated, because the README's compatibility pointer is suppressed by comparing against it
#: (ADR-042) and a second copy of the literal is a second thing to keep in step.
UNKNOWN_VERSION = "0.0.0+unknown"

try:
    __version__ = _package_version("paperclip-blueprints")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = UNKNOWN_VERSION
