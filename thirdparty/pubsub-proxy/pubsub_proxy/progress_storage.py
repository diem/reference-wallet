#!/usr/bin/env python3

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .util import load_custom_backend


class BaseProgressStorage(ABC):
    """
    Base class for accessing storage that saves sync progress

    Used by daemon to track progress.
    Gets updated after successful enqueuing of messages to pubsub broker
    """

    @abstractmethod
    def fetch_state(self) -> Optional[str]:
        ...

    @abstractmethod
    def save_state(self, state: str) -> None:
        ...


class FileProgressStorage(BaseProgressStorage):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.path = config["path"]

    def fetch_state(self) -> Optional[str]:
        try:
            with open(self.path, "r") as file:
                return file.read()
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save_state(self, state: str) -> None:
        with open(self.path, "w") as file:
            file.write(state)


def create_progress_storage(
    storage_type: str, config: Dict[str, Any]
) -> BaseProgressStorage:
    storage_class = {"file": FileProgressStorage}.get(storage_type)
    if storage_class is None:
        storage_class = load_custom_backend(storage_type)
    return storage_class(config)
