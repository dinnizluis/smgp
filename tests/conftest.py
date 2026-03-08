import sys
from pathlib import Path

# Ensure project root is on sys.path so test imports like
# `from infrastructure.database import ...` work regardless of
# how pytest determines its import root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
