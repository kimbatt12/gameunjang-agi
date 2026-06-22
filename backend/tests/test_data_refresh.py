from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.data_refresh import (
    DEFAULT_BACKEND_CURRENT,
    DEFAULT_SCHEMA_PATH,
    METADATA_FILE,
    DataRefreshError,
    generate_staging,
    promote_current,
    smoke_snapshot,
    validate_snapshot,
)


class DataRefreshTests(unittest.TestCase):
    def test_valid_snapshot_promotes_current_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging = root / "staging"
            current = root / "current"
            artifacts = root / "artifacts"

            manifest = generate_staging(DEFAULT_BACKEND_CURRENT, staging)
            validation = validate_snapshot(staging, DEFAULT_SCHEMA_PATH)
            smoke = smoke_snapshot(staging)
            summary = promote_current(staging, current, artifacts)

            self.assertGreaterEqual(manifest["rowCount"], 8)
            self.assertEqual(validation["rowCount"], manifest["rowCount"])
            self.assertEqual(len(smoke["cases"]), 3)
            self.assertTrue((current / METADATA_FILE).is_file())
            self.assertTrue((artifacts / "refresh-summary.json").is_file())
            self.assertEqual(summary["status"], "success")

    def test_failed_validation_preserves_existing_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging = root / "staging"
            current = root / "current"
            artifacts = root / "artifacts"

            generate_staging(DEFAULT_BACKEND_CURRENT, staging)
            promote_current(staging, current, artifacts)
            original_current = (current / METADATA_FILE).read_text(encoding="utf-8")

            invalid_payload = json.loads(original_current)
            invalid_payload["apis"] = []
            (staging / METADATA_FILE).write_text(
                json.dumps(invalid_payload, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaises(DataRefreshError):
                promote_current(staging, current, artifacts)

            self.assertEqual(
                (current / METADATA_FILE).read_text(encoding="utf-8"),
                original_current,
            )

    def test_post_promotion_validation_failure_restores_existing_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging = root / "staging"
            current = root / "current"
            artifacts = root / "artifacts"

            generate_staging(DEFAULT_BACKEND_CURRENT, staging)
            promote_current(staging, current, artifacts)
            original_current = (current / METADATA_FILE).read_text(encoding="utf-8")

            def fail_current_validation(snapshot_dir: Path) -> dict[str, object]:
                if snapshot_dir == current:
                    raise DataRefreshError("current validation failed")
                return validate_snapshot(snapshot_dir)

            with (
                patch(
                    "tools.data_refresh.validate_snapshot",
                    side_effect=fail_current_validation,
                ),
                self.assertRaises(DataRefreshError),
            ):
                promote_current(staging, current, artifacts)

            self.assertEqual(
                (current / METADATA_FILE).read_text(encoding="utf-8"),
                original_current,
            )
            self.assertFalse((root / ".current-backup").exists())

    def test_post_promotion_smoke_failure_restores_existing_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging = root / "staging"
            current = root / "current"
            artifacts = root / "artifacts"

            generate_staging(DEFAULT_BACKEND_CURRENT, staging)
            promote_current(staging, current, artifacts)
            original_current = (current / METADATA_FILE).read_text(encoding="utf-8")

            def fail_current_smoke(snapshot_dir: Path) -> dict[str, object]:
                if snapshot_dir == current:
                    raise DataRefreshError("current smoke failed")
                return smoke_snapshot(snapshot_dir)

            with (
                patch(
                    "tools.data_refresh.smoke_snapshot", side_effect=fail_current_smoke
                ),
                self.assertRaises(DataRefreshError),
            ):
                promote_current(staging, current, artifacts)

            self.assertEqual(
                (current / METADATA_FILE).read_text(encoding="utf-8"),
                original_current,
            )
            self.assertFalse((root / ".current-backup").exists())


if __name__ == "__main__":
    unittest.main()
