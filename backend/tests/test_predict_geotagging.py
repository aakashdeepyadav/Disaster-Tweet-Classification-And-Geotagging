import os
import torch
import pytest

# Ensure tests don't auto-load models/server
os.environ["DISABLE_AUTO_LOAD_MODEL"] = "1"
os.environ["DISABLE_APP_RUN"] = "1"

from disaster_api import app


def make_fake_tokenizer():
    def tokenizer(text, truncation=True, padding=True, max_length=128, return_tensors="pt"):
        return {
            "input_ids": torch.tensor([[1, 2, 3]]),
            "attention_mask": torch.tensor([[1, 1, 1]]),
        }
    return tokenizer


class FakeModel:
    def __init__(self, logits):
        self._logits = logits

    def parameters(self):
        # param with device attr
        p = torch.nn.Parameter(torch.tensor([1.0]))
        yield p

    def __call__(self, **kwargs):
        class Out:
            def __init__(self, logits):
                self.logits = logits
        return Out(self._logits)


def test_no_geotag_for_non_disaster(monkeypatch):
    # Non-disaster logits favor class 0
    model = FakeModel(torch.tensor([[5.0, 0.1]]))
    monkeypatch.setattr(app, "model", model)
    monkeypatch.setattr(app, "tokenizer", make_fake_tokenizer())
    monkeypatch.setattr(app, "device", torch.device("cpu"))

    called = {"geotagged": False}

    def fake_geotag(text):
        called["geotagged"] = True
        return {"lat": 1.0, "lon": 2.0, "location": "X", "location_mention": "X", "source": "geocoded"}

    monkeypatch.setattr(app, "extract_and_geocode", fake_geotag)

    result = app.predict_single("Nice sunny day at the beach")
    assert result["disaster_label"] == 0
    assert result["lat"] is None and result["lon"] is None
    assert called["geotagged"] is False


def test_geotag_for_disaster(monkeypatch):
    # Disaster logits favor class 1
    model = FakeModel(torch.tensor([[0.1, 5.0]]))
    monkeypatch.setattr(app, "model", model)
    monkeypatch.setattr(app, "tokenizer", make_fake_tokenizer())
    monkeypatch.setattr(app, "device", torch.device("cpu"))

    def fake_geotag(text):
        return {"lat": 12.34, "lon": 56.78, "location": "Some City", "location_mention": "Some City", "source": "geocoded"}

    monkeypatch.setattr(app, "extract_and_geocode", fake_geotag)

    result = app.predict_single("Massive fire in Some City")
    assert result["disaster_label"] == 1
    assert result["lat"] == pytest.approx(12.34, rel=1e-3)
    assert result["lon"] == pytest.approx(56.78, rel=1e-3)
    assert result["location"] is not None
