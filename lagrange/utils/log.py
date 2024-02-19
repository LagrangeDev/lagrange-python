import logging

__all__ = ["logger"]


class LoggerProvider:
    def __init__(self, root: logging.Logger = None):
        if not root:
            root = logging.getLogger("lagrange")

        self._root = root
        self._init()

    def _init(self):
        self._login = self._root.getChild("login")
        self._network = self._root.getChild("network")
        self._utils = self._root.getChild("utils")

    def switch(self, _logger):
        if not hasattr(_logger, "getChild"):
            raise NotImplementedError("Logger must have getChild method")
        self._root = _logger
        self._init()

    def fork(self, child_name: str) -> logging.Logger:
        return self._root.getChild(child_name)

    @property
    def root(self) -> logging.Logger:
        return self._root

    @property
    def network(self) -> logging.Logger:
        return self._network

    @property
    def utils(self) -> logging.Logger:
        return self._utils

    @property
    def login(self) -> logging.Logger:
        return self._login


logger = LoggerProvider()
