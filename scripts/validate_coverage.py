from pathlib import Path
import sys
import unittest

from coverage import Coverage


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    cov = Coverage(config_file=str(ROOT / ".coveragerc"))
    cov.erase()
    cov.start()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    cov.stop()
    cov.save()

    if not result.wasSuccessful():
        return 1

    total = cov.report(show_missing=True)
    if total < 34:
        print(f"Coverage {total:.2f}% is below the 34% threshold.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
