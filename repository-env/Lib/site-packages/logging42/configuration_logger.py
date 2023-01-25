"""
Wrapper for retrieving configurations and safely logging their retrieval
"""
import json
import os
import re
from typing import Any
from typing import Callable

from distutils.util import strtobool

from logging42.logger import logger


class Required:
    pass


class ConfigurationValue(str):
    """"""

    def json(self, **kwargs):
        return json.loads(self, **kwargs)

    def bool(self):
        return strtobool(self)

    def int(self):
        return int(self)

    def float(self):
        return float(self)

    def str(self):
        return str(self)


class ConfigurationRetriever:
    """"""

    def __init__(
        self,
        retriever: Callable[[str, Any], str] = os.environ.get,
        secrets: tuple = ("password", "pass", "secret", "token"),
    ):
        self.retriever = retriever
        self.secrets = secrets
        self.configs = {}

    def __call__(self, key, default=Required) -> ConfigurationValue:
        value = self._retrieve_configuration(key, default)
        self.configs = {**self.configs, key: value}
        return ConfigurationValue(value)

    def _retrieve_configuration(self, k, default) -> Any:
        value = self.retriever(k, default)
        if value is Required:
            raise ValueError(f"Configuration value for {k} is required.")
        is_default = value is default
        msg = f"Retrieved value for {k}. is_default={is_default}"
        if is_default:
            logger.warning(msg)
        else:
            logger.debug(msg)
        return value

    def is_secret(self, k: str):
        pattern = "|".join([f"({s.upper()})" for s in self.secrets])
        return bool(re.findall(pattern, k.upper()))

    def __str__(self):
        s = ", ".join(
            [
                f"{k}: <CENSORED>" if self.is_secret(k) else f"{k}: {v}"
                for k, v in self.configs.items()
            ]
        )
        return s

    def log_configs(self):
        logger.info(f"Retrieved configurations: {str(self)}")
