"""Document scanner package: turns a photo of a page into a clean, flat scan."""

from .pipeline import DocumentScanner, ScanResult

__all__ = ["DocumentScanner", "ScanResult"]
