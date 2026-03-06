import sys
from pathlib import Path

# ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# wrap the actual application in a tiny wrapper instance.  Vercel’s
# detector not only looks for a variable named ``app`` but also scans
# for a ``FastAPI()`` call in the AST, so we create a new instance and
# mount the real app at the root path.
from fastapi import FastAPI
from phase4_backend.main import app as real_app

app = FastAPI()
app.mount("/", real_app)
