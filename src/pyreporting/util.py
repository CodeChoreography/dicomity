import inspect
import itertools
import os
import subprocess
import sys


class ReportingException(Exception):
    """Wrapper for exceptions thrown by the Reporting framework"""
    def __init__(self, message, identifier=None):
        super().__init__(message)
        self.identifier = identifier


class UserCancelled(Exception):
    """Custom exception when user has cancelled an operation"""


def get_calling_function(levels_to_ignore):
    """Obtain the name of the function which signalled the error (useful in
    error reporting)"""
    max_levels = 10
    full_stack = inspect.stack()
    for frame in itertools.islice(full_stack, levels_to_ignore, max_levels):
        frame0 = frame[0]
        if hasattr(frame0, "f_code") and hasattr(frame0.f_code, "co_qualname"):
            return frame0.f_code.co_qualname
        elif "self" in frame0.f_locals:
            classname = frame0.f_locals.get('self').__class__.__name__
            fn_name = frame.function
            return ".".join(filter(None, [classname, fn_name]))
        else:
            return frame.function
    return ''


def throw_exception(identifier, message, exception=None):
    if exception:
        raise ReportingException(message=message, identifier=identifier) \
            from exception
    else:
        raise ReportingException(message=message, identifier=identifier)


def open_path(folder_path: str):
    platform = sys.platform
    if platform == 'Windows':
        os.startfile(folder_path)
    elif platform == "darwin":
        subprocess.call(["open", folder_path])
    else:
        subprocess.call(["xdg-open", folder_path])
