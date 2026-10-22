"""Keep the registry manifest consistent with the code, so listings never drift."""

import json
import tomllib
from pathlib import Path

import jsonschema
import pytest

from genebe_mcp import __version__
from genebe_mcp.server import DESCRIPTION

ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "server.json").read_text())


def test_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert MANIFEST["version"] == pyproject["project"]["version"] == __version__


def test_description_is_shared_with_server():
    assert MANIFEST["description"] == DESCRIPTION
    assert len(DESCRIPTION) <= 100  # registry limit


def test_remote_points_at_versioned_endpoint():
    assert MANIFEST["remotes"] == [{"type": "streamable-http", "url": "https://mcp.genebe.net/v1/mcp"}]


def test_matches_registry_schema_when_available():
    schema_file = ROOT / "tests" / "fixtures" / "server.schema.json"
    if not schema_file.exists():
        pytest.skip("registry schema not vendored")
    jsonschema.validate(MANIFEST, json.loads(schema_file.read_text()))
