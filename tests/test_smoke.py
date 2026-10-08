"""Run: python tests/test_smoke.py  - executes every page headlessly and the core engine."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest

pages = ["app.py"] + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "pages").glob("*.py"))
bad = 0
for p in pages:
    at = AppTest.from_file(str(ROOT / p), default_timeout=120).run()
    status = "OK " if not at.exception else "FAIL"
    bad += bool(at.exception)
    print(status, p, [str(e.value)[:300] for e in at.exception])
sys.exit(bad)
