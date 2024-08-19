import inspect
import logging
import sys
from typing import ClassVar, Callable, Optional, Protocol, Union

__all__ = ["log", "install_loguru"]


class Logger(Protocol):
    def info(self, __message: str, *args, **kwargs): ...

    def debug(self, __message: str, *args, **kwargs): ...

    def success(self, __message: str, *args, **kwargs): ...

    def warning(self, __message: str, *args, **kwargs): ...

    def error(self, __message: str, *args, **kwargs): ...

    def critical(self, __message: str, *args, **kwargs): ...

    def exception(self, __message: str, *args, **kwargs): ...

    def set_level(self, level: Union[str, int]): ...


class LoggingLoggerProxy:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self.info = logger.info
        self.debug = logger.debug
        self.success = logger.info
        self.warning = logger.warning
        self.error = logger.error
        self.critical = logger.critical
        self.exception = logger.exception
        self.set_level = logger.setLevel


class _Logger:
    get_logger: ClassVar[Callable[["_Logger"], Logger]]

    def __init__(self, root, context: Optional[str] = None):
        self._root = root
        self.context = context or root.name

    def info(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).debug(msg, *args, **kwargs)

    def success(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).success(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        _Logger.get_logger(self).exception(msg, *args, **kwargs)

    def set_level(self, level: Union[str, int]):
        _Logger.get_logger(self).set_level(level)


_Logger.get_logger = lambda self: LoggingLoggerProxy(self._root)


class LoggerProvider:
    def __init__(self):
        logging.basicConfig(
            level="INFO", format="%(asctime)s | %(name)s[%(levelname)s]: %(message)s"
        )
        self._root = logging.getLogger("lagrange")
        self.loggers: dict[str, _Logger] = {
            "lagrange": _Logger(self._root),
        }
        self.fork("login")
        self.fork("network")
        self.fork("utils")

    def set_level(self, level: Union[str, int]):
        logging.basicConfig(
            level=level, format="%(asctime)s | %(name)s[%(levelname)s]: %(message)s"
        )
        for _, logger in self.loggers.items():
            logger.set_level(level)

    def fork(self, child_name: str):
        logger = _Logger(self._root.getChild(child_name))
        self.loggers[logger.context] = logger
        return logger

    @property
    def root(self) -> _Logger:
        return self.loggers["lagrange"]

    @property
    def network(self) -> _Logger:
        return self.loggers["lagrange.network"]

    @property
    def utils(self) -> _Logger:
        return self.loggers["lagrange.utils"]

    @property
    def login(self) -> _Logger:
        return self.loggers["lagrange.login"]


log = LoggerProvider()


def install_loguru():
    from loguru import logger

    class LoguruHandler(logging.Handler):  # pragma: no cover
        """logging 与 loguru 之间的桥梁，将 logging 的日志转发到 loguru。"""

        def emit(self, record: logging.LogRecord):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = inspect.currentframe(), 0
            while frame and (
                depth == 0 or frame.f_code.co_filename == logging.__file__
            ):
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(
        handlers=[LoguruHandler()],
        level="INFO",
        format="%(asctime)s | %(name)s[%(levelname)s]: %(message)s",
    )

    def default_filter(record):
        log_level = record["extra"].get("lagrange_log_level", "INFO")
        levelno = (
            logger.level(log_level).no if isinstance(log_level, str) else log_level
        )
        return record["level"].no >= levelno

    logger.remove()
    logger.add(
        sys.stderr,
        level=0,
        diagnose=True,
        backtrace=True,
        colorize=True,
        filter=default_filter,
        format="<g>{time:MM-DD HH:mm:ss}</g> | <lvl>{level: <8}</lvl> | <c><u>{name}</u></c> | <lvl>{message}</lvl>",
    )

    def _config(level: Union[str, int]):
        logging.basicConfig(
            handlers=[LoguruHandler()],
            level=level,
            format="%(asctime)s | %(name)s[%(levelname)s]: %(message)s",
        )
        logger.configure(extra={"lagrange_log_level": level})

    log.set_level = _config

    _Logger.get_logger = lambda self: logger.patch(
        lambda r: r.update(name=self.context)
    )
