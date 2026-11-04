"""Exercise the dashboard with actual Streamlit runtime and generated artifacts."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


@unittest.skipIf(AppTest is None, "Install requirements-reporting.txt for dashboard checks")
class DashboardTests(unittest.TestCase):
    def test_real_reports_filter_and_detail_view(self):
        if not (ROOT / "reports/p5/reports.json").exists():
            self.skipTest("Generate the real P5 report before integration testing")
        app = AppTest.from_file(str(ROOT / "app/reporting_dashboard.py"), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(len(app.selectbox[0].options), 0)
        app.selectbox[0].select_index(1).run()
        self.assertEqual(len(app.exception), 0)
        app.sidebar.text_input[1].set_value("NO_SUCH_ISSUE_987654321").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Không có vấn đề" in message.value for message in app.info))
        app.sidebar.text_input[1].set_value("").run()
        app.sidebar.checkbox[0].check().run()
        self.assertEqual(len(app.exception), 0)

    def test_missing_output_shows_recovery_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = AppTest.from_file(str(ROOT / "app/reporting_dashboard.py"), default_timeout=60).run()
            app.sidebar.text_input[0].set_value(temporary).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("run_reporting.py" in block.value for block in app.code))


if __name__ == "__main__":
    unittest.main()
