#!/usr/bin/env python3
"""
ArBanking77-Verify v0.1.1

Reference implementation of a generic benchmark-state compatibility check.
It verifies immutable source identities, materializes tabular records from
local files or pinned URLs/ZIP members, and compares historical vs current
record multisets through a declared normalization ladder.

Standard-library only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

TOOL_VERSION = "0.1.1"
PROFILE_SCHEMA_VERSION = "1.0"

AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
WS = re.compile(r"\s+")
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"


class VerifyError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _norm_nfkc_ws(value: str) -> str:
    return WS.sub(" ", unicodedata.normalize("NFKC", value)).strip()


def _norm_arabic_light(value: str) -> str:
    s = _norm_nfkc_ws(value)
    s = AR_DIAC.sub("", s)
    s = s.replace("ـ", "")
    s = re.sub("[إأآٱ]", "ا", s)
    s = s.replace("ى", "ي")
    s = s.replace("ؤ", "و").replace("ئ", "ي")
    return WS.sub(" ", s).strip()


def _strip_punctuation(value: str) -> str:
    return "".join(ch for ch in value if not unicodedata.category(ch).startswith("P"))


def normalize(value: str, mode: str) -> str:
    if mode == "exact":
        return value
    if mode == "nfkc_ws":
        return _norm_nfkc_ws(value)
    if mode == "arabic_light":
        return _norm_arabic_light(value)
    if mode == "arabic_light_punct":
        return WS.sub(" ", _strip_punctuation(_norm_arabic_light(value))).strip()
    raise VerifyError(f"Unknown normalization mode: {mode}")


def compare_multisets(historical: list[str], current: list[str], mode: str) -> dict[str, int | str]:
    hist = Counter(normalize(v, mode) for v in historical)
    curr = Counter(normalize(v, mode) for v in current)
    shared = sum((hist & curr).values())
    return {
        "mode": mode,
        "historical_rows": len(historical),
        "current_rows": len(current),
        "shared_multiset_rows": shared,
        "historical_unmatched": len(historical) - shared,
        "current_only": len(current) - shared,
        "net_row_difference": len(current) - len(historical),
    }


def load_profile(path: Path) -> dict[str, Any]:
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise VerifyError(f"Could not read profile {path}: {exc}") from exc
    validate_profile(profile, source=str(path))
    return profile


def validate_profile(profile: dict[str, Any], source: str = "<profile>") -> None:
    required = ["schema_version", "profile_id", "benchmark", "state_role", "records", "sources"]
    missing = [key for key in required if key not in profile]
    if missing:
        raise VerifyError(f"{source}: missing profile fields: {', '.join(missing)}")
    if profile["schema_version"] != PROFILE_SCHEMA_VERSION:
        raise VerifyError(
            f"{source}: unsupported schema_version={profile['schema_version']!r}; "
            f"expected {PROFILE_SCHEMA_VERSION!r}"
        )
    if not isinstance(profile["profile_id"], str) or not profile["profile_id"].strip():
        raise VerifyError(f"{source}: profile_id must be a non-empty string")
    records = profile["records"]
    if not isinstance(records, dict) or not isinstance(records.get("text_column"), str):
        raise VerifyError(f"{source}: records.text_column is required")
    if "expected_rows" in records and (
        not isinstance(records["expected_rows"], int) or records["expected_rows"] < 0
    ):
        raise VerifyError(f"{source}: records.expected_rows must be a non-negative integer")
    sources = profile["sources"]
    if not isinstance(sources, list) or not sources:
        raise VerifyError(f"{source}: sources must be a non-empty list")
    seen: set[str] = set()
    for item in sources:
        if not isinstance(item, dict):
            raise VerifyError(f"{source}: each source must be an object")
        sid = item.get("source_id")
        if not isinstance(sid, str) or not sid:
            raise VerifyError(f"{source}: every source requires source_id")
        if sid in seen:
            raise VerifyError(f"{source}: duplicate source_id={sid!r}")
        seen.add(sid)
        has_url = isinstance(item.get("url"), str) and bool(item["url"])
        has_path = isinstance(item.get("path"), str) and bool(item["path"])
        if has_url == has_path:
            raise VerifyError(
                f"{source}: source {sid!r} must declare exactly one of url or path"
            )
        if "member" in item and not isinstance(item["member"], str):
            raise VerifyError(f"{source}: source {sid!r} member must be a string")
        for field in ("sha256", "member_sha256"):
            if field in item and not re.fullmatch(r"[0-9a-f]{64}", str(item[field]).lower()):
                raise VerifyError(f"{source}: source {sid!r} has invalid {field}")
        if "git_blob_sha1" in item and not re.fullmatch(
            r"[0-9a-f]{40}", str(item["git_blob_sha1"]).lower()
        ):
            raise VerifyError(f"{source}: source {sid!r} has invalid git_blob_sha1")


def _cache_path(cache_dir: Path, source: dict[str, Any]) -> Path:
    suffix = Path(source.get("url") or source.get("path") or source["source_id"]).suffix
    key = hashlib.sha256(
        (source.get("url") or source.get("path") or source["source_id"]).encode("utf-8")
    ).hexdigest()[:24]
    return cache_dir / f"{source['source_id']}-{key}{suffix}"


def _download(url: str, dst: Path, timeout: int = 120) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"ArBanking77-Verify/{TOOL_VERSION}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise VerifyError(f"Upstream source unavailable: {url}: {exc}") from exc
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return data


def obtain_source_bytes(
    source: dict[str, Any], cache_dir: Path, offline: bool
) -> tuple[bytes, dict[str, Any]]:
    if "path" in source:
        path = Path(source["path"]).expanduser().resolve()
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise VerifyError(f"Could not read local source {path}: {exc}") from exc
        obtained_from = str(path)
    else:
        cache_path = _cache_path(cache_dir, source)
        if cache_path.exists():
            data = cache_path.read_bytes()
            obtained_from = str(cache_path)
        elif offline:
            raise VerifyError(
                f"Offline mode: no cached copy for source {source['source_id']!r}"
            )
        else:
            data = _download(source["url"], cache_path)
            obtained_from = source["url"]

    if data.startswith(LFS_PREFIX):
        raise VerifyError(
            f"Source {source['source_id']!r} is a Git LFS pointer, not dataset bytes"
        )

    report: dict[str, Any] = {
        "source_id": source["source_id"],
        "obtained_from": obtained_from,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "git_blob_sha1": git_blob_sha1(data),
    }

    expected_sha = source.get("sha256")
    if expected_sha and report["sha256"] != expected_sha.lower():
        raise VerifyError(
            f"SHA-256 mismatch for {source['source_id']!r}: "
            f"expected {expected_sha}, got {report['sha256']}"
        )
    expected_blob = source.get("git_blob_sha1")
    if expected_blob and report["git_blob_sha1"] != expected_blob.lower():
        raise VerifyError(
            f"Git blob SHA-1 mismatch for {source['source_id']!r}: "
            f"expected {expected_blob}, got {report['git_blob_sha1']}"
        )
    return data, report


def read_member(data: bytes, source: dict[str, Any], report: dict[str, Any]) -> bytes:
    member = source.get("member")
    if not member:
        return data
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            if member not in names:
                raise VerifyError(
                    f"ZIP member {member!r} not found in source {source['source_id']!r}; "
                    f"available entries={len(names)}"
                )
            member_data = archive.read(member)
    except zipfile.BadZipFile as exc:
        raise VerifyError(f"Source {source['source_id']!r} is not a valid ZIP") from exc

    if member_data.startswith(LFS_PREFIX):
        raise VerifyError(
            f"ZIP member {member!r} in {source['source_id']!r} is a Git LFS pointer"
        )

    report["member"] = member
    report["member_bytes"] = len(member_data)
    report["member_sha256"] = sha256_bytes(member_data)
    report["member_git_blob_sha1"] = git_blob_sha1(member_data)
    expected = source.get("member_sha256")
    if expected and report["member_sha256"] != expected.lower():
        raise VerifyError(
            f"Member SHA-256 mismatch for {source['source_id']!r}/{member}: "
            f"expected {expected}, got {report['member_sha256']}"
        )
    return member_data


def decode_csv(data: bytes, source_id: str) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise VerifyError(
        f"Source {source_id!r} is not valid UTF-8/UTF-8-with-BOM CSV"
    )


def records_from_csv(data: bytes, text_column: str, source_id: str) -> list[str]:
    text = decode_csv(data, source_id)
    stream = io.StringIO(text, newline="")
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise VerifyError(f"Source {source_id!r} has no CSV header")
    if text_column not in reader.fieldnames:
        raise VerifyError(
            f"Source {source_id!r} lacks text column {text_column!r}; "
            f"columns={reader.fieldnames}"
        )
    rows: list[str] = []
    try:
        for row_number, row in enumerate(reader, start=2):
            value = row.get(text_column)
            if value is None:
                raise VerifyError(
                    f"Source {source_id!r} row {row_number} lacks {text_column!r}"
                )
            rows.append(value)
    except csv.Error as exc:
        raise VerifyError(f"CSV parse failure in {source_id!r}: {exc}") from exc
    return rows


def materialize_profile(
    profile: dict[str, Any], cache_dir: Path, offline: bool
) -> tuple[list[str], list[dict[str, Any]]]:
    text_column = profile["records"]["text_column"]
    combined: list[str] = []
    reports: list[dict[str, Any]] = []
    for source in profile["sources"]:
        data, report = obtain_source_bytes(source, cache_dir, offline)
        payload = read_member(data, source, report)
        rows = records_from_csv(payload, text_column, source["source_id"])
        report["records_loaded"] = len(rows)
        combined.extend(rows)
        reports.append(report)

    expected_rows = profile["records"].get("expected_rows")
    if expected_rows is not None and len(combined) != expected_rows:
        raise VerifyError(
            f"Profile {profile['profile_id']!r} row-count mismatch: "
            f"expected {expected_rows}, got {len(combined)}"
        )
    return combined, reports


def profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": profile["schema_version"],
        "profile_id": profile["profile_id"],
        "benchmark": profile["benchmark"],
        "state_role": profile["state_role"],
        "source_commit": profile.get("source_commit"),
        "record_scope": profile.get("record_scope"),
        "expected_rows": profile["records"].get("expected_rows"),
    }


def run_compare(args: argparse.Namespace) -> int:
    historical = load_profile(Path(args.historical))
    current = load_profile(Path(args.current))
    if historical["benchmark"] != current["benchmark"]:
        raise VerifyError(
            f"Benchmark mismatch: {historical['benchmark']!r} vs {current['benchmark']!r}"
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache)
    cache_dir.mkdir(parents=True, exist_ok=True)

    hist_rows, hist_sources = materialize_profile(historical, cache_dir, args.offline)
    curr_rows, curr_sources = materialize_profile(current, cache_dir, args.offline)

    ladder = ["exact", "nfkc_ws", "arabic_light", "arabic_light_punct"]
    comparisons = [compare_multisets(hist_rows, curr_rows, mode) for mode in ladder]

    report = {
        "tool": "ArBanking77-Verify",
        "tool_version": TOOL_VERSION,
        "comparison_semantics": (
            "Multiplicity-preserving multiset comparison of the declared text columns. "
            "A passing source-identity check establishes the bytes used; it does not "
            "by itself prove semantic correctness of upstream data."
        ),
        "historical_profile": profile_summary(historical),
        "current_profile": profile_summary(current),
        "normalization_ladder": comparisons,
    }
    source_report = {
        "tool_version": TOOL_VERSION,
        "historical_profile": historical["profile_id"],
        "historical_sources": hist_sources,
        "current_profile": current["profile_id"],
        "current_sources": curr_sources,
    }
    (out / "comparison.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "source_manifest.json").write_text(
        json.dumps(source_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def run_materialize(args: argparse.Namespace) -> int:
    profile = load_profile(Path(args.profile))
    rows, reports = materialize_profile(profile, Path(args.cache), args.offline)
    result = {
        "tool_version": TOOL_VERSION,
        "profile": profile_summary(profile),
        "observed_rows": len(rows),
        "sources": reports,
    }
    if args.out:
        Path(args.out).write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def run_validate_profile(args: argparse.Namespace) -> int:
    profile = load_profile(Path(args.profile))
    print(json.dumps({"valid": True, "profile": profile_summary(profile)}, indent=2))
    return 0


def run_hash(args: argparse.Namespace) -> int:
    path = Path(args.path)
    data = path.read_bytes()
    result = {
        "path": str(path),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "git_blob_sha1": git_blob_sha1(data),
    }
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arbanking77-verify",
        description=(
            "Verify benchmark-state source identities and compare record multisets."
        ),
    )
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-profile", help="Validate a state profile")
    validate.add_argument("profile")
    validate.set_defaults(func=run_validate_profile)

    materialize = sub.add_parser(
        "materialize", help="Fetch/verify a profile and report its observed row count"
    )
    materialize.add_argument("profile")
    materialize.add_argument("--cache", default=".cache/arbanking77-verify")
    materialize.add_argument("--out")
    materialize.add_argument("--offline", action="store_true")
    materialize.set_defaults(func=run_materialize)

    compare = sub.add_parser(
        "compare", help="Compare historical and current state profiles"
    )
    compare.add_argument("--historical", required=True)
    compare.add_argument("--current", required=True)
    compare.add_argument("--cache", default=".cache/arbanking77-verify")
    compare.add_argument("--out", default="artifacts/arbanking77-verify")
    compare.add_argument("--offline", action="store_true")
    compare.set_defaults(func=run_compare)

    hash_cmd = sub.add_parser("hash", help="Report byte SHA-256 and Git blob SHA-1")
    hash_cmd.add_argument("path")
    hash_cmd.set_defaults(func=run_hash)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except VerifyError as exc:
        print(f"VERIFY ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"I/O ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
