"""
Tests for the configuration logger
"""
from os import environ

import pytest

from logging42.configuration_logger import ConfigurationRetriever


secrets = ("password", "pass", "secret", "token")


def keys() -> list:
    start = []
    middle = []
    end = []
    for s in secrets:
        start += [f"{s}safe", f"{s.upper()}safe"]
        middle += [f"safe{s}safe", f"safe{s.upper()}safe"]
        end += [f"safe{s}", f"safe{s.upper()}"]

    return start + middle + end


@pytest.fixture(scope="function")
def configuration_retriever():
    return ConfigurationRetriever(secrets=secrets)


@pytest.mark.parametrize("key", keys())
def test_censoring(configuration_retriever, key):
    configuration_retriever(key, "default")
    assert str(configuration_retriever) == f"{key}: <CENSORED>"


def test_safe(configuration_retriever):
    configuration_retriever("safe", "default")
    assert str(configuration_retriever) == f"safe: default"


@pytest.mark.parametrize(
    "env_variable, output_bool", [("True", True), ("False", False), ("1", True), ("0", False)]
)
def test_bool(env_variable, output_bool):
    environ["TEST_BOOL_VARIABLE"] = env_variable
    config = ConfigurationRetriever()
    assert config("TEST_BOOL_VARIABLE").bool() == output_bool


def test_int():
    environ["TEST_INT_VARIABLE"] = "5"
    config = ConfigurationRetriever()
    assert config("TEST_INT_VARIABLE").int() == 5


def test_float():
    environ["TEST_FLOAT_VARIABLE"] = "3.86"
    config = ConfigurationRetriever()
    assert config("TEST_FLOAT_VARIABLE").float() == 3.86
