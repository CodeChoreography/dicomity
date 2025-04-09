import logging
from os.path import join
from pathlib import Path
from typing import Optional

from platformdirs import user_log_dir

from pyreporting.util import get_calling_function


class Logger:
    def __init__(self, app_name: Optional[str] = None,
                 debug: bool = False, log_filename: Optional[str] = None):
        """Initialise logging to console and log file.

        Args:
            app_name: Name of application to use when creating log directory.
                If both app_name and log_filename are unspecified, the log
                file will be disabled and output will be to the console only
            debug: if True, log debug messages, otherwise they will be ignored
            log_filename: Full path to log file to create instead of using the
                default log directory specified by app_name
        """
        log_level = logging.DEBUG if debug else logging.INFO

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')

        if app_name and not log_filename:
            log_dir = user_log_dir(appname=app_name, appauthor=False)
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            log_filename = join(log_dir, app_name) + ".log"

        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)

        stderr_handler = logging.StreamHandler()  # Log to stderr by default
        stderr_handler.setLevel(log_level)
        stderr_handler.setFormatter(formatter)
        self.logger.addHandler(stderr_handler)

        if log_filename:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.info(f"Log file for {app_name} {log_filename}")

    def log(self, level: int, prefix: str, identifier: str, message: str,
            supplementary_info: str, exception):
        """Write a message to the console and log file

        Args:
            level: Logging level (using Python logging library constants)
            prefix: Optional description of the message type (e.g. "warning")
            identifier: Optional error code/identifier
            message: Message to write
            supplementary_info: optional additional info to append to message
            exception: Optional Exception, if the entry relates to an exception
        """
        self.logger.log(
            level=level,
            msg=self._format(
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                prefix=prefix,
                calling_level=4
            ),
            exc_info=exception)

    @staticmethod
    def default_log(level: int, prefix: str, identifier: str, message: str,
                    supplementary_info: str, exception):
        """Write a message to the console and log file

        Args:
            level: Logging level (using Python logging library constants)
            prefix: Optional description of the message type (e.g. "warning")
            identifier: Optional error code/identifier
            message: Message to write
            supplementary_info: optional additional info to append to message
            exception: Optional Exception, if the entry relates to an exception
        """
        logging.getLogger().log(
            level=level,
            msg=Logger._format(
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                prefix=prefix,
                calling_level=3
            ),
            exc_info=exception)

    @staticmethod
    def _format(identifier, message, supplementary_info, prefix,
                calling_level: int):
        calling_function = get_calling_function(calling_level)
        full_prefix = " from ".join(filter(None, [prefix, calling_function]))
        message = ": ".join(filter(None, [full_prefix, identifier, message]))
        if supplementary_info:
            message = message \
                      + " Additional information on this message: " \
                      + supplementary_info
        return message
