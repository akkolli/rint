"""Regression checks for accidental inclusion in a source release."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "release_check", Path(__file__).parents[1] / "rint-release-check.py"
)
release_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_check)


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_private_env_is_blocked_even_when_supplied_as_tracked(self):
        (self.root / ".env.rint").write_text("private configuration")
        self.assertTrue(release_check.inspect_file(self.root, ".env.rint"))
        (self.root / ".env.example").write_text("APP_SECRET_KEY=change-me")
        self.assertEqual(release_check.inspect_file(self.root, ".env.example"), [])

    def test_secret_content_is_found_without_returning_the_secret(self):
        secret = "ghp_" + "a" * 36
        (self.root / "config.py").write_text('token = "' + secret + '"')
        findings = release_check.inspect_file(self.root, "config.py")
        self.assertEqual(findings, ["GitHub credential"])
        self.assertNotIn(secret, str(findings))

    def test_documents_and_external_symlinks_cannot_slip_into_release(self):
        (self.root / "resume.pdf").write_bytes(b"document")
        self.assertTrue(release_check.inspect_file(self.root, "resume.pdf"))
        (self.root / "outside").symlink_to(self.root.parent / "private-data")
        self.assertTrue(release_check.inspect_file(self.root, "outside"))

    def test_missing_tracked_file_does_not_crash(self):
        self.assertEqual(release_check.inspect_file(self.root, "removed.py"), [])


if __name__ == "__main__":
    unittest.main()
