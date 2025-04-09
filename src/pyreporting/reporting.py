from dataclasses import dataclass
from logging import DEBUG, ERROR, INFO, WARNING
from typing import Callable, Optional

from pyreporting.logger import Logger
from pyreporting.progress import Progress
from pyreporting.progress_bar import ProgressBarType
from pyreporting.util import open_path, throw_exception


class Reporting:
    """Provides error, message and progress reporting.

    Reporting is a class used to process errors, warnings, messages,
    logging information and progress bars. This means that warnings,
    errors and progress are handled via a callback instead of
    directly bringing up message boxes and progress boxes or writing to the
    command window. This allows applications to choose how they
    process error, warning and progress information.

    Typically, a single Reporting object is created during application startup,
    and passed into the classes and functions that use it. This means that
    logging and progress reporting are handled in a single place, allowing for
    consistent behaviour across the application and more advanced features such
    as nested progress dialogs.

    The default Reporting implementation uses the standard python logging
    library, so standard logging calls should also work.

    Progress can be provided via a console progress bar (TerminalProgress) for
    terminal applications, or a windowed progress bar for GUI applications.

    You can create your own implementation of the Reporting interface to get
    customised message and progress behaviour; for example, if you are running
    a batch script you may wish it to run silently, whereas for a GUI
    application you may wish to display error, warning and progress dialogs
    to the user.
    """

    CancelErrorId = 'CoreReporting:UserCancel'

    USE_TERMINAL_PROGRESS = "USER_TERMINAL_PROGRESS"

    def __init__(
            self,
            app_name: str = "pyreporting_default",
            progress_type: Optional[ProgressBarType] = ProgressBarType.TERMINAL,
            log_file_name=None, debug=False):
        """

        Args:
            app_name: Application name to use when creating log file directory
            progress_type: Either an object implementing the Progress
                 interface, None for no progress, or a ProgressBarType enum
                 which will be used to determine which progress bar to create
            log_file_name: Specify log filename instead of using default
                application log file directory based on app_name
            debug: set to True to log debug messages
        """
        if not isinstance(progress_type, ProgressBarType):
            raise ValueError(f"progress_type should be a ProgressBarType enum")

        self.progress = Progress(progress_type=progress_type)
        self.logger = Logger(
            app_name=app_name,
            debug=debug,
            log_filename=log_file_name
        )
        self.app_name = app_name
        self.cache = RecordCache(log_function=self.logger.log)
        self.enabled_cache_types = []

    def __del__(self):
        self.end_message_caching()

    def debug(self,
              message: str,
              identifier: str = None,
              supplementary_info: str = None,
              exception=None):
        """Write debugging information to the console and log file"""
        self.logger.log(
            level=DEBUG,
            prefix="Debug info",
            identifier=identifier,
            message=message,
            supplementary_info=supplementary_info,
            exception=exception
        )

    def info(self,
             message: str,
             identifier: str = None,
             supplementary_info: str = None,
             exception=None):
        """Write an information message to the console and log file"""
        if INFO in self.enabled_cache_types:
            self.cache.add(
                level=INFO,
                prefix="Info",
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                exception=exception
            )
        else:
            self.logger.log(
                level=INFO,
                prefix="Info",
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                exception=exception
            )

    def warning(self,
                message: str,
                identifier: str = None,
                supplementary_info: str = None,
                exception=None):
        """Write a warning message to the console and log file"""
        if WARNING in self.enabled_cache_types:
            self.cache.add(
                level=WARNING,
                prefix="Warning",
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                exception=exception
            )
        else:
            self.logger.log(
                level=WARNING,
                prefix="Warning",
                identifier=identifier,
                message=message,
                supplementary_info=supplementary_info,
                exception=exception
            )

    def error(self,
              message: str,
              identifier: str = None,
              supplementary_info=None,
              exception=None,
              throw: bool = True):
        """Write an error message to the console and log file.
        If throw is True, this will also raise an exception. Where appropriate,
        the application should catch this exception and present the message to
        the user e.g. using a modal error dialog"""
        self.logger.log(
            level=ERROR,
            prefix="Error",
            identifier=identifier,
            message=message,
            supplementary_info=supplementary_info,
            exception=exception
        )
        if throw:
            throw_exception(message=message, identifier=identifier,
                            exception=exception)

    @staticmethod
    def default_error(message: str,
                      identifier: str = None,
                      supplementary_info=None,
                      exception=None,
                      throw: bool = True):
        """Write an error message to the console and log file.
        If throw is True, this will also raise an exception. Where appropriate,
        the application should catch this exception and present the message to
        the user e.g. using a modal error dialog"""
        Logger.default_log(
            level=ERROR,
            prefix="Error",
            identifier=identifier,
            message=message,
            supplementary_info=supplementary_info,
            exception=exception
        )
        if throw:
            throw_exception(message=message, identifier=identifier,
                            exception=exception)

    @staticmethod
    def default_warning(message: str,
                        identifier: str = None,
                        supplementary_info=None,
                        exception=None):
        """Write a warning message to the console and log file"""
        Logger.default_log(
            level=WARNING,
            prefix="Warning",
            identifier=identifier,
            message=message,
            supplementary_info=supplementary_info,
            exception=exception
        )

    def start_message_caching(self, cache_types: Optional[list[int]] = None):
        """Enable message caching to prevent duplicate log messages

        This typically is used with WARNING and INFO messages.

        When caching is on, messages will not be displayed or logged but will
        be added to the cache.

        When show_and_clear_pending_messages() is called, the messages in the
        cache will be displayed, but messages with the same identifier will
        only be shown once, with the message modified to show how many times
        the message was generated.

        This helps to stop the command window or log file being overwhelmed
        with duplicate warning or info messages

        Start caching messages of specified types (typically WARNING and
        INFO). Instead of immediately displaying/logging these messages, they
        will be grouped to prevent multiple messages of the same type from

        Args:
            cache_types: list of warning levels to cache. Currently supports
                WARNING and INFO.
        """
        self.enabled_cache_types = cache_types if cache_types is not None \
            else [INFO, WARNING]

    def end_message_caching(self):
        """End the message caching started by end_message_caching()

        This will show any pending error or warning log messages, with adjusted
        message text to show the number of repetitions of duplicate messages.
        """
        self.cache.show_and_clear()
        self.enabled_cache_types = []

    def show_progress(self, text='Please wait', value=0, title='',
                      hold: bool = False):
        """Initialise progress dialog
        Unlike update_progress(), any values not specified (left as None) will
        be given default values and will not retain their previous values

        Args:
            text: Text to display in progress bar
            value: Current progress bar value, initialise at 0
            title: Title text for the progress dialog
            hold: set to True to keep progress visible until hide() is called
        """
        self.progress.show(label=text, value=value, title=title, hold=hold)

    def complete_progress(self):
        """Complete the progress dialog, and hide unless Hold is set to True"""
        self.progress.complete()

    def hide_progress(self):
        """Hide the progress dialog"""
        self.progress.hide()

    def update_progress(self, label: Optional[str] = None,
                        value: Optional[int] = None,
                        title: Optional[str] = None,
                        step: Optional[int] = None):
        """Update values in the progress dialog
        Unlike show_progress(), any values not specified (left as None) will
        retain their previous values

        Args:
            label: Text to display in progress bar
            value: Current progress bar value, initialise at 0
            title: Title text for the progress dialog
            step: The percentage change between progress updates. This is used
                when generating nested progress updates
        """
        self.progress.update(value=value, step=step, label=label, title=title)

    def update_progress_message(self, text: str):
        """Change the subtext in the progress dialog"""
        self.progress.update(label=text)

    def update_progress_value(self, progress_value: int):
        """Change the percentage complete in the progress dialog, displaying if
        necessary"""
        self.progress.update(value=progress_value)

    def update_progress_stage(self,
                              progress_stage: int,
                              num_stages: int,
                              label: Optional[str] = None,
                              title: Optional[str] = None):
        """When progress reporting consists of a number of stages, use this
        method to ensure progress is handled correctly"""
        self.progress.update_stage(
            stage=progress_stage, num_stages=num_stages, label=label,
            title=title)

    def update_progress_and_message(self, progress_value, text):
        """Change the percentage complete and message in the progress dialog,
        displaying if necessary"""
        self.progress.update(value=progress_value, label=text)

    def has_been_cancelled(self) -> bool:
        """Return True if the user has clicked Cancel in the progress dialog"""
        return self.progress.has_been_cancelled()

    def check_for_cancel(self):
        """Raise Cancel exception if user has clicked Cancel"""
        self.progress.check_for_cancel()

    def push_progress(self):
        """Nest progress reporting. After calling this function, subsequent
        progress updates will modify the progress bar between the current
        value ane the current value plus the last value_change."""
        self.progress.push()

    def pop_progress(self):
        """Remove one layer of nested progress nesting, returning to the
        previous progress reporting."""
        self.progress.pop()

    def clear_progress_stack(self):
        """Clear all progress nesting"""
        self.progress.clear_progress_stack()

    def open_path(self, file_path, message):
        # ToDo: Should be implemented where a decision can be made as to whether
        # this is in a gui environment
        open_path(file_path)

    def set_progress_parent(self, parent):
        """Set the parent window handle for progress dialogs"""
        self.progress.set_progress_parent(parent)


DEFAULT_REPORTING: Optional['Reporting'] = None


def get_reporting(error_if_not_configured: bool = False) -> Reporting:
    global DEFAULT_REPORTING
    if DEFAULT_REPORTING is not None:
        return DEFAULT_REPORTING
    if error_if_not_configured:
        raise RuntimeError("Default Reporting object has not been configured")
    return configure_reporting()


def configure_reporting(
        app_name: str = "pyreporting_default",
        progress_type: Optional[ProgressBarType] = ProgressBarType.TERMINAL,
        log_file_name=None,
        debug=False) -> Reporting:
    global DEFAULT_REPORTING
    if DEFAULT_REPORTING is not None:
        DEFAULT_REPORTING.error(
            identifier='Reporting:DefaultAlreadyConfigured',
            message='Reporting.configure_default() was called but the '
                    'default Reporting object has already been configured',
            throw=True
        )
    DEFAULT_REPORTING = Reporting(
        app_name=app_name,
        progress_type=progress_type,
        log_file_name=log_file_name,
        debug=debug
    )
    return DEFAULT_REPORTING


@dataclass
class PendingRecord:
    level: int
    prefix: str
    identifier: str
    text: str
    supplementary_info: str
    exception: Exception
    count: int = 1


class RecordCache:
    def __init__(self, log_function: Callable):
        self.log_function = log_function
        self.cache = {}

    def add(self, level, prefix, identifier, message, supplementary_info, exception):
        key = f"{level}.{identifier}"
        if key in self.cache:
            self.cache[key].count += 1
        else:
            self.cache[key] = PendingRecord(
                level=level,
                prefix=prefix,
                identifier=identifier,
                text=message,
                supplementary_info=supplementary_info,
                exception=exception
            )

    def show_and_clear(self):
        for _, record in self.cache.items():
            message = record.text
            if record.count > 1:
                message = f'(repeated x{record.count}) {record.text}'
            self.log_function(
                level=record.level,
                prefix=record.prefix,
                identifier=record.identifier,
                message=message,
                supplementary_info=record.supplementary_info,
                exception=record.exception
            )
        self.cache.clear()
