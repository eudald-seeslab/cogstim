import sys
from pathlib import Path

# Ensure parent directory (project root) is on sys.path for test execution
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
