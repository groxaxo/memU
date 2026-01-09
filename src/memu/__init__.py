try:
    from memu._core import hello_from_bin

    def _rust_entry() -> str:
        return hello_from_bin()
except ImportError:
    # Rust core not built, skip for now
    def _rust_entry() -> str:
        return "Rust core not available"

# Make key components available for import
__all__ = ["_rust_entry"]
