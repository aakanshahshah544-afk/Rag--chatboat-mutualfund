import sys
from pathlib import Path

# Make sure the project root is on the path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app defined in phase4_backend
from phase4_backend.main import app

# Vercel uses the variable named "app" as the ASGI application.
# No additional code is required; the existing routes and startup logic
# from phase4_backend.main will be used directly.
