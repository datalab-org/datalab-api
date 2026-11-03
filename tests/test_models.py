# This file was edited with the assistance of an AI model and requires human review from the contributor.
import datetime as dt
import json
from typing import Optional

import pytest
from httpx2 import Response
from pydantic import ValidationError

from datalab_api import DatalabClient
from datalab_api.models import DatalabItem, DatalabModel, build_item_models, model_from_schema


@pytest.fixture
def models(fake_item_types_json):
    return build_item_models(fake_item_types_json)


def test_build_item_models_offline(models):
    assert set(models) == {
        "samples",
        "cells",
        "starting_materials",
        "equipment",
        "_my_samples",
        "_my_items",
    }
    assert set(models.custom_types) == {"_my_samples", "_my_items"}

    Sample, MySample, MyItem = models.Sample, models.MySample, models.MyItem  # noqa: N806
    assert models["_my_samples"] is MySample
    assert models["samples"].item_type == "samples"

    # Custom types subclass their declared base type, where it is available
    assert issubclass(MySample, Sample)
    assert MySample.base_type == "samples"
    assert not issubclass(MyItem, Sample)
    assert issubclass(MyItem, DatalabItem)
    assert MyItem.base_type == "items"
    assert MySample.ui_color == "#ff8800"
    assert MySample.hidden_fields == ["synthesis_description"]

    assert {"drying_time", "custom_properties"} <= set(MySample.model_fields)
    assert "drying_time" not in Sample.model_fields
    assert "chemform" not in MyItem.model_fields

    # Shared nested models are exposed and reused across item types
    constituents = Sample.model_fields["synthesis_constituents"].annotation
    assert constituents == Optional[list[models.Constituent]]  # noqa: UP045
    assert MySample.model_fields["synthesis_constituents"].annotation == constituents
    assert issubclass(models.File, DatalabModel)

    # Can also build from a plain mapping of type -> schema
    from_mapping = build_item_models({"samples": models.Sample.datalab_schema})
    assert list(from_mapping) == ["samples"]

    with pytest.raises(KeyError, match="available types"):
        models["_nonexistent"]
    with pytest.raises(AttributeError, match="available item models"):
        _ = models.Nonexistent


def test_local_validation(models):
    sample = models.MySample(
        name="test",
        drying_time=2.5,
        custom_properties={"batch": "A"},
        synthesis_constituents=[{"item": {"name": "NaCl"}, "quantity": 1}],
    )
    assert sample.item_id is None
    assert sample.type == "_my_samples"
    assert type(sample.custom_properties).__name__ == "CustomProperties"
    assert sample.synthesis_constituents[0].item.name == "NaCl"
    assert sample.synthesis_constituents[0].unit == "g"

    # Dict-style access for backwards-compatibility
    assert sample["drying_time"] == 2.5
    assert sample.get("missing", "default") == "default"
    assert "GHS_codes" in sample

    with pytest.raises(ValidationError):
        sample.status = "not-a-status"
    with pytest.raises(ValidationError):
        models.MySample(item_id="no spaces allowed")
    with pytest.raises(ValidationError):
        models.Sample(type="cells")

    # In-place mutations are validated before anything is sent
    sample.synthesis_constituents.append({"quantity": -1})
    with pytest.raises(ValidationError):
        sample.changes()


def test_field_name_sanitisation():
    model = model_from_schema(
        {
            "title": "Odd Names",
            "type": "object",
            "properties": {
                "schema": {"type": "string"},
                "class": {"type": "integer"},
                "_private": {"type": "boolean"},
                "model_type": {"type": "string"},
                "1st": {"type": "string"},
                "with space": {"type": "string"},
            },
        }
    )
    assert model.__name__ == "OddNames"
    instance = model.model_validate(
        {
            "schema": "a",
            "class": 1,
            "_private": True,
            "model_type": "b",
            "1st": "c",
            "with space": "d",
        }
    )
    assert instance["schema"] == "a"
    assert instance.class_ == 1
    assert instance["_private"] is True
    assert instance.model_type == "b"
    assert instance["1st"] == "c"
    assert instance["with space"] == "d"
    assert instance.to_dict() == {
        "schema": "a",
        "class": 1,
        "_private": True,
        "model_type": "b",
        "1st": "c",
        "with space": "d",
    }


def test_from_api_fallback(models):
    with pytest.warns(UserWarning, match="does not validate"):
        sample = models.Sample.from_api({"item_id": "bad", "type": "samples", "status": "bogus"})
    assert sample.status == "bogus"
    assert sample.is_synced


def test_models_lazy_loading(mocked_api, fake_api_url):
    with DatalabClient(fake_api_url) as client:
        assert not mocked_api["info-types"].called
        assert client.models.Sample.datalab_client is client
        assert mocked_api["info-types"].called
        assert client.item_types_info
        assert client.models is client.models

        # Existing methods still return dicts by default
        assert isinstance(client.get_item("KUVEKJ"), dict)


def test_get_item_as_model(mocked_api, fake_api_url):
    with DatalabClient(fake_api_url, use_models=True) as client:
        sample = client.get_item("KUVEKJ")
        assert isinstance(sample, client.models.Sample)
        assert sample.item_id == "KUVEKJ"
        assert sample["refcode"] == "demo:KUVEKJ"
        assert isinstance(sample.date, dt.datetime)
        assert isinstance(sample.files[0], client.models.File)
        assert [b.blocktype for b in sample.blocks] == ["ms"]
        assert sample.client is client
        assert sample.changes() == {}

        # Can be overridden per call
        assert isinstance(client.get_item("KUVEKJ", as_model=False), dict)

        # Summaries are also returned as models, retaining extra fields
        items = client.get_items()
        assert isinstance(items[0], client.models.Sample)
        assert items[0]["nblocks"] == 0

        # Display still works for models
        client.get_item("KUVEKJ", display=True)
        client.get_items(display=True)


def test_save(mocked_api, fake_api_url):
    sent = []

    def _save(request):
        sent.append(json.loads(request.content))
        return Response(200, json={"status": "success", "last_modified": "2026-11-03T12:00:00"})

    mocked_api["bad-save"].side_effect = _save

    with DatalabClient(fake_api_url) as client:
        sample = client.get_item("KUVEKJ", as_model=True)
        sample.name = "renamed"
        sample.synthesis_constituents.append({"item": {"name": "NaCl"}, "quantity": 2})

        changes = sample.save()
        assert sent == [{"item_id": "KUVEKJ", "data": changes}]
        assert set(changes) == {"name", "synthesis_constituents"}
        assert changes["synthesis_constituents"][0]["quantity"] == 2
        assert sample.last_modified == dt.datetime(2026, 11, 3, 12)
        assert sample.changes() == {}

        # Nothing to send if nothing has changed
        assert sample.save() == {}
        assert len(sent) == 1

        # Passing a model to `update_item` also only sends changes
        sample.description = "new"
        client.update_item("KUVEKJ", sample)
        assert sent[-1] == {"item_id": "KUVEKJ", "data": {"description": "new"}}

        with pytest.raises(RuntimeError, match="already exists"):
            sample.create()

        with pytest.raises(RuntimeError, match="not been created"):
            client.models.Sample(item_id="new").save()


def test_create(mocked_api, fake_api_url):
    with DatalabClient(fake_api_url) as client:
        MySample = client.models.MySample  # noqa: N806
        sample = MySample(name="My custom sample", drying_time=1.5)
        assert not sample.is_synced
        assert sample.create() is sample

        payload = json.loads(mocked_api["new-sample"].calls.last.request.content)
        assert payload["generate_id_automatically"] is True
        assert payload["new_sample_data"] == {
            "name": "My custom sample",
            "drying_time": 1.5,
            "type": "_my_samples",
        }

        assert sample.is_synced
        assert sample.item_id == "NEWITM"
        assert sample.refcode == "test:NEWITM"
        assert sample.immutable_id == "6808d7fb47ccfd57b44da999"
        assert sample.drying_time == 1.5
        assert sample.changes() == {}

        # Creating via the client method with a model and an explicit ID
        created = client.create_item(item_data=client.models.MyItem(item_id="abc", width=3.0))
        assert isinstance(created, dict)
        payload = json.loads(mocked_api["new-sample"].calls.last.request.content)
        assert payload["generate_id_automatically"] is False
        assert payload["new_sample_data"] == {"item_id": "abc", "width": 3.0, "type": "_my_items"}

        created = client.create_item(item_id="xyz", item_type="_my_items", as_model=True)
        assert isinstance(created, client.models.MyItem)

        with pytest.raises(ValueError, match="does not match"):
            client.create_item(item_type="cells", item_data=MySample())


def test_unknown_type_returns_dict(mocked_api, fake_api_url, fake_samples_json):
    fake_samples_json["samples"][0]["type"] = "_unregistered"
    mocked_api["samples"].return_value = Response(200, json=fake_samples_json)
    with DatalabClient(fake_api_url) as client:
        with pytest.warns(UserWarning, match="No model available"):
            items = client.get_items(as_model=True)
        assert isinstance(items[0], dict)
