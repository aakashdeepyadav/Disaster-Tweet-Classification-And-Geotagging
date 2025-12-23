import os
import pytest

# Disable auto model loading and server run to allow importing app without models
os.environ["DISABLE_AUTO_LOAD_MODEL"] = "1"
os.environ["DISABLE_APP_RUN"] = "1"

from disaster_api import app


def test_health_check():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "online"
    assert "model_loaded" in data
    assert "geotagging_available" in data
