import sys
import pathlib

# Ensure the project root directory is on the Python path so that `import app.*` works
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Override DB URL for tests to avoid postgres dependency
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db") 