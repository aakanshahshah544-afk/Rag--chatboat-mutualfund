import sys
from pathlib import Path

# Make sure the project root is on the path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app defined in phase4_backend.  We alias it to
# `_app` so that we can expose a clean top‑level name below; some
# automated tools (including the FastAPI entrypoint detector used by
# Vercel/other platforms) look for a literal assignment to ``app`` in
# the file rather than an imported symbol.
from phase4_backend.main import app as _app

# expose the imported application under the expected name
app = _app

# Vercel uses the variable named "app" as the ASGI application.
# No additional code is required; the existing routes and startup logic
# from phase4_backend.main will be used directly.
