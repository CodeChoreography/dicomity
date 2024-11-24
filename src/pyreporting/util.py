import inspect
import itertools

from pyreporting.core import CoreException


def get_calling_function(levels_to_ignore):
    """Obtain the name of the function which signalled the error (useful in
    error reporting)"""
    max_levels = 10
    full_stack = inspect.stack()
    for frame in itertools.islice(full_stack, levels_to_ignore, max_levels):
        calling_function = frame.function
        if not calling_function.startswith('CoreReporting'):
            return calling_function
    return ''


@staticmethod
def throw_exception(identifier, message, exception=None):
    if exception:
        raise CoreException(message=message, identifier=identifier) \
            from exception
    else:
        raise CoreException(message=message, identifier=identifier)
