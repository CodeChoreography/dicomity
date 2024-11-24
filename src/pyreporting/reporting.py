from os.path import join
from pathlib import Path

from dicomity.util import current_date_string, get_user_directory
from pyreporting.progress import TerminalProgress, ProgressStackItem
from pyreporting.util import get_calling_function, throw_exception


class Reporting:
    """Provides an interface for error and progress reporting.

    Reporting is the interface used to process errors, warnings, messages,
    logging information and progress reports. This means that warnings,
    errors and progress are handled via a callback instead of
    directly bringing up message and progress boxes or writing to the
    command window. This allows applications to choose how they
    process error, warning and progress information.

    You can create your own implementation of this interface to get
    customised message behaviour; for example, if you are running a batch
    script you may wish to write all messages to a log file instead of
    displaying them on the command line.

    This is an abstract class; you should not directly create an instance
    of Reporting. Instead, you should either use one of the
    existing implementation classes (CoreReporting, CoreReportingDefault) or
    you can create your own to achieve customised behaviour.
    """

    def log(self, identifier, message):
        """Write debugging information to the log file"""
        raise NotImplementedError

    def logVerbose(self, identifier, message):
        """Write debugging information to the log file, but only if in verbose
        mode"""
        raise NotImplementedError

    # Displays an information message to the user. This will generally be
    # written to the command window
    def showMessage(self, identifier, message, supplementary_info=None):
        raise NotImplementedError

    # Displays a warning to the user. This will generally be
    # written to the command window.
    def showWarning(self, identifier, message, supplementary_info=None):
        raise NotImplementedError

    # Displays an error to the user. This may trigger an
    # exception which will ultimately be displayed to the user as a modal
    # error dialog or written to the command window,
    def error(self, identifier, message):
        raise NotImplementedError

    # Displays an error to the user. Similar to Error() but also displays
    # additional information about an exception which triggered the error.
    def errorFromException(self, identifier, message, ex):
        raise NotImplementedError

    # Displays the progress dialog with the specified title
    def show_progress(self, text):
        raise NotImplementedError

    # Hides the progress dialog
    def completeProgress(self):
        raise NotImplementedError

    # Changes the subtext in the progress dialog
    def updateProgressMessage(self, text):
        raise NotImplementedError

    # Changes the percentage complete in the progress dialog, displaying if
    # necessary
    def updateProgressValue(self, progress_value):
        raise NotImplementedError

    # When progress reporting consists of a number of stages, use this
    # method to ensure progress is handled correctly
    def updateProgressStage(self, progress_stage, num_stages):
        raise NotImplementedError

    # Changes the percentage complete and subtext in the progress dialog,
    # displaying if necessary
    def updateProgressAndMessage(self, progress_value, text):
        raise NotImplementedError

    def hasBeenCancelled(self):
        """Used to check if the user has clicked the cancel button in the
        progress dialog"""
        raise NotImplementedError

    def checkForCancel(self):
        """Force an exception if the user has clicked cancel in the progress
        dialog"""
        raise NotImplementedError

    def pushProgress(self):
        """Nests progress reporting. After calling this function, subsequent
        progress updates will modify the progress bar between the current
        value ane the current value plus the last value_change."""
        raise NotImplementedError

    def popProgress(self):
        """Remove one layer of progress nesting, returning to the previous
        progress reporting."""
        raise NotImplementedError

    def clearProgressStack(self):
        """Clear all progress nesting"""
        raise NotImplementedError

    def showAndClearPendingMessages(self):
        """Show any error or warning messages and clear the message stack"""
        raise NotImplementedError


class ReportingBase(Reporting):
    """Provides error, message and progress reporting.

    Implementation of Reporting, which is used by
    CoreMat and other libraries for progress and error/message reporting. This
    implementation displays warnings and messages on the command window,
    and uses Matlab's error() command to process errors. Logging
    information is writen to a log file. An object which implements
    the Progress can be passed in for progress reporting.

    Usage
    -----

    You should create a single CoreReporting object and pass it into all the
    CoreMat routines you use in order to provide error, warning,
    message and progress reporting during execution of routines.

    If you are not writing a gui application but would like a standard
    pop-up progress dialog to appear while waiting for plugins to execute,
    consider creating a CoreReportingDefault object instead. Use CoreReporting
    if you want to specify your own progress dialog, or specify a gui
    viewing panel, or if you want no progress dialog at all.

        reporting = CoreReporting(progress_dialog, viewing_panel);

            progress_dialog - a Progress object such as
                a TerminalProgress for displaying a progress bar. You can
                omit this argument
                or replace it with None if you are writing scripts to run
                in the background and do not want progress dialogs popping
                up. Otherwise, you should create a CoreProgressDialog
                or else implement your own progress class if you want
                custom behaviour.

    See reporting.py for details of the methods this class implements.
    """

    CancelErrorId = 'CoreReporting:UserCancel'

    def __init__(self, progress_dialog=None,
                 verbose_mode=False,
                 log_file_name=None):

        # Handle to a ProgressInterface object
        self.ProgressDialog = progress_dialog

        self.VerboseMode = verbose_mode
        Path(get_user_directory()).mkdir(parents=True,
                                                     exist_ok=True)
        if not log_file_name:
            log_file_name = join(get_user_directory(),
                                 'reporting.log')
        self.LogFileName = log_file_name

        # self.ProgressStack = []
        # self.CurrentProgressStackItem = CoreProgressStackItem('', 0, 100)
        # self.ParentProgressStackItem = CoreProgressStackItem('', 0, 100)
        self.clearProgressStack()

    # properties (Access = private)
    #     LogFileName     # Full path to log file
    #
    #     # Stack for nested progress reporting
    #     ProgressStack
    #     CurrentProgressStackItem
    #     ParentProgressStackItem
    #     VerboseMode
    # end
    #

    def log(self, identifier, message):
        calling_function = get_calling_function(2)
        self._appendToLogFile(f'{calling_function}: {identifier}: {message}')

    def log_verbose(self, identifier, message):
        if self.VerboseMode:
            calling_function = get_calling_function(2)
            self._appendToLogFile(
                f'{calling_function}: {identifier}: {message}')

    def show_message(self, identifier, message, supplementary_info=None):
        calling_function = get_calling_function(2)
        if not calling_function:
            calling_function = 'Command Window'
        print(message)

        self._appendToLogFile(f'{calling_function}: {identifier}: {message}')

        if supplementary_info:
            print('Additional information on this message:')
            print(supplementary_info)

    def show_message_from_exception(self, identifier, message, ex):
        calling_function = get_calling_function(2)
        if not calling_function:
            calling_function = 'Command Window'
        message = f'{calling_function}: {identifier}: {message}; ' \
                  f'Exception message:{ex.message} : {ex.stack(1).name}'
        summary, stack_text = self._getExceptionSummary(ex)

        self._appendToLogFile(message)
        self._appendToLogFile(summary)
        self._appendToLogFile(stack_text)
        print(message)
        print(' ')
        print('If reporting an error, please include the following '
              'information:')
        print(f'  {summary}')
        print(f'  {stack_text} \n')
        print(' ')

    def show_warning(self, identifier, message, supplementary_info=None):
        calling_function = get_calling_function(2)

        self._appendToLogFile(f'{calling_function}: '
                              f'WARNING: {identifier}:{message}')
        print(f'WARNING: {message}')
        if supplementary_info:
            print('Additional information on this warning:')
            print(supplementary_info)

    def error(self, identifier, message):
        calling_function = get_calling_function(2)

        message_text = f'Error in function {calling_function}: {message}'
        self._appendToLogFile(f'{calling_function}: '
                              f'ERROR: {identifier}:{message}')

        throw_exception(message=message_text, identifier=identifier)

    def error_from_exception(self, identifier, message, ex):
        calling_function = get_calling_function(2)

        summary, stack_text = self._getExceptionSummary(ex)
        message_text = f'Error in function {calling_function}: {identifier}: ' \
                       f'{message}; Exception message: {str(ex)}'

        self._appendToLogFile(message_text)
        self._appendToLogFile(summary)
        self._appendToLogFile(stack_text)

        print(message_text)
        print(' ')
        print('If reporting an error, please include the following information')
        print('  ' + summary)
        print('  ' + stack_text)
        print(' ')

        throw_exception(message=message_text, identifier=identifier,
                        exception=ex)

    def show_progress(self, text=None):
        adjusted_text = self._adjustProgressText(text)

        if self.ProgressDialog:
            self.ProgressDialog.set_progress_text(adjusted_text)
            self.CurrentProgressStackItem.visible = True

    def complete_progress(self):
        if self.ProgressDialog:
            if not self.ProgressStack or \
                    not self.ParentProgressStackItem.visible:
                self.ProgressDialog.complete()
                self.CurrentProgressStackItem.visible = False

    def update_progress_message(self, text):
        adjusted_text = self._adjustProgressText(text)

        if self.ProgressDialog:
            self.ProgressDialog.set_progress_text(adjusted_text)
            self.CurrentProgressStackItem.visible = True

    def update_progress_value(self, progress_value):
        adjusted_value = self._adjustProgressValue(progress_value, None)

        if self.ProgressDialog:
            self.ProgressDialog.set_progress_value(adjusted_value)
            self.CurrentProgressStackItem.visible = True
        self.checkForCancel()

    def updateProgressStage(self, progress_stage, num_stages):
        progress_value = 100*progress_stage/num_stages
        value_change = 100/num_stages
        adjusted_value = self._adjustProgressValue(progress_value, value_change)
        if self.ProgressDialog:
            self.ProgressDialog.SetProgressValue(adjusted_value)
            self.CurrentProgressStackItem.visible = True
        self.checkForCancel()

    def updateProgressAndMessage(self, progress_value, text):
        adjusted_value = self._adjustProgressValue(progress_value, None)
        adjusted_text = self._adjustProgressText(text)

        if self.ProgressDialog:
            self.ProgressDialog.set_progress_and_message(adjusted_value,
                                                         adjusted_text)
            self.CurrentProgressStackItem.visible = True

        self.checkForCancel()

    def hasBeenCancelled(self):
        if self.ProgressDialog:
            return self.ProgressDialog.cancel_clicked()
        else:
            return False

    def checkForCancel(self):
        if self.hasBeenCancelled():
            self.error(ReportingBase.CancelErrorId, 'User cancelled')

    def push_progress(self):
        self.ProgressStack.append(self.ParentProgressStackItem)
        self.ParentProgressStackItem = self.CurrentProgressStackItem
        self.CurrentProgressStackItem = ProgressStackItem(
            progress_text='',
            min_position=self.ParentProgressStackItem.min_position,
            max_position=self.ParentProgressStackItem.max_position,
            visible=self.ParentProgressStackItem.visible
        )

    def popProgress(self):
        self.CurrentProgressStackItem = self.ParentProgressStackItem
        if not self.ProgressStack:
            self.ParentProgressStackItem = None
        else:
            self.ParentProgressStackItem = self.ProgressStack.pop()

    def clearProgressStack(self):
        self.ProgressStack = []
        self.CurrentProgressStackItem = ProgressStackItem('', 0, 100)
        self.ParentProgressStackItem = ProgressStackItem('', 0, 100)

    def showAndClearPendingMessages(self):
        pass

    def openPath(self, file_path, message):
        print(f'{message}: {file_path}')

    def _appendToLogFile(self, message):
        message = current_date_string() + ': ' + message
        with open(self.LogFileName, 'a') as file:
            file.write(message)

    @staticmethod
    def _getExceptionSummary(exc):
        stack = 'Stack: TODO'
        # stack = 'Stack:' + traceback.format_exc(exc)
        summary = 'Summary: TODO'
        # summary = f'Error in {exc.stack(1).name} (CORE {CORE_VERSION}) : ' \
        #           f'{exc.message}'
        return summary, stack

    def _adjustProgressText(self, text):
        adjusted_text = text
        self.CurrentProgressStackItem.progress_text = text
        return adjusted_text

    def _adjustProgressValue(self, value, value_change=None):
        if not value_change:
            value_change = value - \
                           self.CurrentProgressStackItem.last_progress_value
        self.CurrentProgressStackItem.last_progress_value = value

        scale = (self.ParentProgressStackItem.max_position -
                 self.ParentProgressStackItem.min_position) / 100
        adjusted_value = self.ParentProgressStackItem.min_position + scale*value
        self.CurrentProgressStackItem.min_position = adjusted_value
        if value_change > 0:
            self.CurrentProgressStackItem.max_position = adjusted_value + \
                                                         scale * value_change
        return adjusted_value

    def _setValueChange(self, value_change):
        value = self.CurrentProgressStackItem.last_progress_value
        scale = (self.ParentProgressStackItem.max_position -
                 self.ParentProgressStackItem.min_position) / 100
        adjusted_value = self.ParentProgressStackItem.min_position + scale*value
        self.CurrentProgressStackItem.min_position = adjusted_value
        if value_change > 0:
            self.CurrentProgressStackItem.max_position = adjusted_value + \
                                                         scale * value_change


class ReportingDefault(ReportingBase):
    """Provides error, message and progress reporting.

    CoreReporting. Implementation of Reporting, which is used by
    CoreMat and related libraries for progress and error/message reporting. This
    is a convenient implementation with no constructor arguments which
    creates a progress dialog and writes messages to the command window,
    but which has no callbacks to the gui.

    This class is intended for use by CoreMat library functions
    when no reporting object is given. It can also be used in your code
    to create a default progress reporting implementation for input into
    CoreMat and related libraries.

    See reporting.py for details of the methods this class
    implements."""

    def __init__(self):
        super().__init__(TerminalProgress())
