from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openinvoice.core.fields import MetadataField


class DummySerializer(serializers.Serializer):
    metadata = MetadataField()


def test_metadata_length_validator():
    data = {"metadata": {f"k{i}": "v" for i in range(21)}}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {"metadata": [ErrorDetail("Invalid metadata length.", code="invalid_metadata_length")]}


def test_metadata_key_validator():
    data = {"metadata": {"k" * 51: "v"}}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {"metadata": [ErrorDetail("Invalid metadata key.", code="invalid_metadata_key")]}


def test_metadata_value_validator():
    data = {"metadata": {"key": "v" * 301}}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {"metadata": [ErrorDetail("Invalid metadata value.", code="invalid_metadata_value")]}


def test_metadata_valid():
    data = {"metadata": {"key": "value"}}
    serializer = DummySerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == {"metadata": {"key": "value"}}


def test_metadata_key_non_string():
    data = {"metadata": {1: "value"}}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {"metadata": [ErrorDetail("Invalid metadata key.", code="invalid_metadata_key")]}


def test_metadata_value_non_string():
    data = {"metadata": {"key": 1}}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {"metadata": [ErrorDetail("Invalid metadata value.", code="invalid_metadata_value")]}


def test_metadata_not_dict():
    data = {"metadata": ["not", "a", "dict"]}
    serializer = DummySerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors == {
        "metadata": [
            ErrorDetail("Invalid metadata key.", code="invalid_metadata_key"),
            ErrorDetail("Invalid metadata value.", code="invalid_metadata_value"),
        ]
    }


def test_metadata_length_boundary():
    data = {"metadata": {f"k{i}": "v" for i in range(20)}}
    serializer = DummySerializer(data=data)
    assert serializer.is_valid()


def test_metadata_key_length_boundary():
    data = {"metadata": {"k" * 50: "v"}}
    serializer = DummySerializer(data=data)
    assert serializer.is_valid()


def test_metadata_value_length_boundary():
    data = {"metadata": {"key": "v" * 300}}
    serializer = DummySerializer(data=data)
    assert serializer.is_valid()


def test_metadata_empty_valid():
    data = {"metadata": {}}
    serializer = DummySerializer(data=data)
    assert serializer.is_valid()
