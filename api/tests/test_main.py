import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

import main as app_module
from main import app, FASTVEP_URL

client = TestClient(app)

FAKE_RESULT = {
    "count": 1,
    "time_ms": 1.0,
    "results": [
        {
            "seq_region_name": "chr1",
            "start": 100,
            "end": 100,
            "allele_string": "A/G",
            "most_severe_consequence": "intergenic_variant",
            "transcript_consequences": [],
        }
    ],
}


@respx.mock
def test_annotate_success():
    respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        return_value=httpx.Response(200, json=FAKE_RESULT)
    )
    resp = client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


@respx.mock
def test_annotate_passes_acmg_flag():
    route = respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        return_value=httpx.Response(200, json=FAKE_RESULT)
    )
    client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}], "acmg": False},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["acmg"] is False


@respx.mock
def test_annotate_acmg_true_by_default():
    route = respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        return_value=httpx.Response(200, json=FAKE_RESULT)
    )
    client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["acmg"] is True


def test_annotate_invalid_body():
    resp = client.post("/annotate", json={"foo": "bar"})
    assert resp.status_code == 422


@respx.mock
def test_annotate_backend_connect_error():
    respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        side_effect=httpx.ConnectError("refused")
    )
    resp = client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    assert resp.status_code == 503


@respx.mock
def test_annotate_empty_body_returns_502():
    respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        return_value=httpx.Response(200, content=b"")
    )
    resp = client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    assert resp.status_code == 502


@respx.mock
def test_annotate_non_json_returns_502():
    respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        return_value=httpx.Response(200, content=b"<html>not json</html>")
    )
    resp = client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    assert resp.status_code == 502


@respx.mock
def test_health_ok():
    respx.get(f"{FASTVEP_URL}/api/status").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "backend": "ok"}


@respx.mock
def test_health_backend_down():
    respx.get(f"{FASTVEP_URL}/api/status").mock(
        side_effect=httpx.ConnectError("refused")
    )
    resp = client.get("/health")
    assert resp.status_code == 503


@respx.mock
def test_annotate_timeout_returns_504():
    respx.post(f"{FASTVEP_URL}/api/annotate").mock(
        side_effect=httpx.TimeoutException("timed out")
    )
    resp = client.post(
        "/annotate",
        json={"variants": [{"chr": "chr1", "pos": 100, "ref": "A", "alt": "G"}]},
    )
    assert resp.status_code == 504
