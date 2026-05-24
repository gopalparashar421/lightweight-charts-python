"""run_tests.py -- legacy runner. CI uses: uv run python -m pytest test/ -v"""

import subprocess
import sys

if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, "-m", "pytest", "test/", "-v"]).returncode)
