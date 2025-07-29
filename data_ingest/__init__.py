from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except ImportError:
    # Graceful degradation – if python-dotenv is not installed, skip auto-load.
    # Modules that rely on env vars will behave as before (may raise their own errors).
    def load_dotenv(*_args, **_kwargs):  # type: ignore
        return False

    def find_dotenv(*_args, **_kwargs):  # type: ignore
        return ""

# ---------------------------------------------------------------------------
# Auto-load environment variables once when the data_ingest package is imported.
# ---------------------------------------------------------------------------

# Search upwards for the first .env file (project root preferred).
# If not found, also try data_ingest/.env (package-local example setup).
_env_path = None

# 1) Standard recursive search (respect `dotenv` default conventions)
try:
    _env_path = Path(find_dotenv(usecwd=True)) if find_dotenv() else None
except Exception:  # noqa: BLE001
    _env_path = None

# 2) Fallback to package-local .env
if not _env_path:
    candidate = Path(__file__).resolve().parent / ".env"
    if candidate.exists():
        _env_path = candidate

if _env_path:
    load_dotenv(dotenv_path=_env_path, override=False)

__all__ = [] 