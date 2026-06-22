from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised by CLI environments only
    Draft202012Validator = None  # type: ignore[assignment]


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DEFAULT_DATA_ROOT = REPO_ROOT / "data"
DEFAULT_BACKEND_CURRENT = BACKEND_ROOT / "app/routing/data/current"
DEFAULT_SCHEMA_PATH = (
    BACKEND_ROOT / "app/routing/data/schemas/tour_api_metadata.schema.json"
)
METADATA_FILE = "tour_api_metadata.json"
REQUIRED_API_IDS = frozenset(
    {
        "area_based_list",
        "search_keyword",
        "detail_common",
        "search_festival",
        "search_stay",
        "restaurant_area",
        "tour_course",
        "area_code",
    }
)
SMOKE_CASES = (
    ("부산 실내 관광지 추천", "area_based_list"),
    ("이번 달 서울 행사 뭐 있어?", "search_festival"),
    ("강릉 2박 3일 코스 짜줘", "tour_course"),
)


class DataRefreshError(RuntimeError):
    """Raised when a data refresh step cannot complete safely."""


def generate_staging(source_dir: Path, staging_dir: Path) -> dict[str, Any]:
    """Create a fresh staging snapshot from the latest trusted source."""
    source_file = source_dir / METADATA_FILE
    if not source_file.is_file():
        raise DataRefreshError(f"source metadata file is missing: {source_file}")

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    payload = _read_json(source_file)
    payload["generatedAt"] = _utc_now_iso()
    for api in payload.get("apis", []):
        api["lastCheckedAt"] = datetime.now(UTC).date().isoformat()

    staging_file = staging_dir / METADATA_FILE
    staging_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "source": _display_path(source_file),
        "generatedAt": payload["generatedAt"],
        "rowCount": len(payload.get("apis", [])),
        "metadataFile": METADATA_FILE,
    }
    (staging_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"staging snapshot generated: {staging_file} rows={manifest['rowCount']}")
    return manifest


def validate_snapshot(
    snapshot_dir: Path,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    minimum_rows: int = len(REQUIRED_API_IDS),
) -> dict[str, Any]:
    """Validate schema, row count, required ids, uniqueness, and dates."""
    metadata_file = snapshot_dir / METADATA_FILE
    if not metadata_file.is_file():
        raise DataRefreshError(f"metadata file is missing: {metadata_file}")
    if not schema_path.is_file():
        raise DataRefreshError(f"schema file is missing: {schema_path}")
    if Draft202012Validator is None:
        raise DataRefreshError("jsonschema is required for data snapshot validation")

    payload = _read_json(metadata_file)
    schema = _read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        ).validate(payload)
    except Exception as exc:
        message = getattr(exc, "message", str(exc))
        raise DataRefreshError(f"schema validation failed: {message}") from exc

    apis = payload["apis"]
    ids = [api["id"] for api in apis]
    missing = REQUIRED_API_IDS - set(ids)
    if len(apis) < minimum_rows:
        raise DataRefreshError(
            f"row count {len(apis)} is below minimum required count {minimum_rows}"
        )
    if len(ids) != len(set(ids)):
        raise DataRefreshError("metadata contains duplicate api ids")
    if missing:
        raise DataRefreshError(
            f"metadata is missing required api ids: {sorted(missing)}"
        )

    datetime.fromisoformat(payload["generatedAt"].replace("Z", "+00:00"))
    result = {
        "snapshot": str(snapshot_dir),
        "schema": str(schema_path.relative_to(REPO_ROOT)),
        "rowCount": len(apis),
        "requiredIds": sorted(REQUIRED_API_IDS),
    }
    print(f"snapshot validation passed: {snapshot_dir} rows={len(apis)}")
    return result


def smoke_snapshot(snapshot_dir: Path) -> dict[str, Any]:
    """Run critical metadata smoke checks without external API calls."""
    payload = _read_json(snapshot_dir / METADATA_FILE)
    apis_by_id = {api["id"]: api for api in payload["apis"]}
    results = []

    for query, expected_id in SMOKE_CASES:
        api = apis_by_id.get(expected_id)
        if api is None:
            raise DataRefreshError(f"smoke failed for '{query}': missing {expected_id}")
        if not _query_matches_api(query, api):
            message = (
                f"smoke failed for '{query}': "
                f"{expected_id} lacks matching routing terms"
            )
            raise DataRefreshError(message)
        results.append({"query": query, "expectedApiId": expected_id})

    result = {"snapshot": str(snapshot_dir), "cases": results}
    print(f"snapshot smoke passed: {snapshot_dir} cases={len(results)}")
    return result


def promote_current(
    staging_dir: Path, current_dir: Path, artifact_dir: Path
) -> dict[str, Any]:
    """Atomically replace current from a validated staging snapshot."""
    validate_snapshot(staging_dir)
    smoke_snapshot(staging_dir)

    current_dir.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    replacement_dir = current_dir.parent / ".current-next"
    backup_dir = current_dir.parent / ".current-backup"

    if replacement_dir.exists():
        shutil.rmtree(replacement_dir)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    shutil.copytree(staging_dir, replacement_dir)

    replaced_at = _utc_now_iso()
    had_current = current_dir.exists()
    try:
        if had_current:
            current_dir.rename(backup_dir)
        replacement_dir.rename(current_dir)
        validate_snapshot(current_dir)
        smoke_snapshot(current_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
    except Exception as exc:
        if replacement_dir.exists():
            shutil.rmtree(replacement_dir)
        if current_dir.exists() and (backup_dir.exists() or not had_current):
            shutil.rmtree(current_dir)
        if backup_dir.exists() and not current_dir.exists():
            backup_dir.rename(current_dir)
        raise DataRefreshError(
            "current replacement failed; previous current restored"
        ) from exc

    summary = {
        "status": "success",
        "replacedAt": replaced_at,
        "currentPath": _display_path(current_dir),
        "stagingPath": _display_path(staging_dir),
        "rowCount": len(_read_json(current_dir / METADATA_FILE)["apis"]),
        "artifacts": ["refresh-summary.json", METADATA_FILE, "manifest.json"],
    }
    (artifact_dir / "refresh-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "current replacement succeeded: "
        f"{summary['currentPath']} rows={summary['rowCount']}"
    )
    print(f"data refresh artifacts written: {artifact_dir}")
    return summary


def _query_matches_api(query: str, api: dict[str, Any]) -> bool:
    searchable_terms = " ".join(
        str(term)
        for field in ("name", "description", "searchText")
        for term in ([api[field]] if api.get(field) else [])
    )
    searchable_terms += " " + " ".join(api.get("synonyms", []))
    searchable_terms += " " + " ".join(api.get("regions", []))
    return any(token in searchable_terms for token in query.split() if len(token) >= 2)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    data_root = Path(args.data_root).resolve()
    source_dir = Path(args.source_dir).resolve()
    staging_dir = data_root / "staging"
    current_dir = data_root / "current"
    artifact_dir = data_root / "artifacts"
    return source_dir, staging_dir, current_dir, artifact_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh validated data snapshots.")
    parser.add_argument(
        "command",
        choices=(
            "generate-staging",
            "validate-staging",
            "smoke-staging",
            "promote",
            "validate-current",
            "smoke-current",
        ),
    )
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    parser.add_argument("--source-dir", default=str(DEFAULT_BACKEND_CURRENT))
    args = parser.parse_args()

    source_dir, staging_dir, current_dir, artifact_dir = _paths(args)
    if args.command == "generate-staging":
        generate_staging(source_dir, staging_dir)
    elif args.command == "validate-staging":
        validate_snapshot(staging_dir)
    elif args.command == "smoke-staging":
        smoke_snapshot(staging_dir)
    elif args.command == "promote":
        promote_current(staging_dir, current_dir, artifact_dir)
    elif args.command == "validate-current":
        validate_snapshot(current_dir)
    elif args.command == "smoke-current":
        smoke_snapshot(current_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
