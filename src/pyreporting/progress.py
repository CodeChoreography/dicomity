from dataclasses import dataclass

from tqdm import tqdm

from dicomity.util import remove_html


class Progress:
    """Interface for classes which implement a progress bar.

    The Reporting class uses this interface to display and update a
    progress bar and associated text. The ProgressDialog class
    implements the progress bar as a standard Matlab progress dialog,
    whereas other implementations may implement a custom progress panel for an
    existing figure.

    You can implement custom progress reporting by creating a class which
    implements this interface, and then passing an instance of your
    progress class into Reporting.
    """

    def resize(self, panel_position):
        """Indicates the gui has been resized"""
        raise NotImplementedError
           
    def show_and_hold(self, text):
        """Show the progress bar, and keep it displayed until hide() called"""

    def hide(self):
        """Hide the progress bar"""
        raise NotImplementedError

    def complete(self):
        """Call to complete a progress operation, which will also hide the
        dialog unless the dialog has been held by show_and_hold()"""
        raise NotImplementedError

    def set_progress_text(self, text):
        """Change the subtext in the progress dialog"""
        raise NotImplementedError

    def set_progress_value(self, progress_value):
        """Changes the value of the progress bar"""
        raise NotImplementedError

    def set_progress_and_message(self, progress_value, text):
        """Change the value of the progress bar and the subtext"""
        raise NotImplementedError

    def cancel_clicked(self):
        """Check if the cancel button was clicked by the user"""
        raise NotImplementedError


class TerminalProgress(Progress):
    """A dialog used to report progress information

    TerminalProgress creates and manages a waitbar to mark progress
    in operations performed by libraries and applications which use
    pyreporting.
    It provides a default implementation of
    Progress that can be used by your own code or can be
    instantiated automatically be functions when no progress
    interface object is provided.

    GUI applications may prefer to create their own implementation of
    Progress which matches their application, rather
    than using this default implementation
    """

    def __init__(self):
        self.IncrementThreshold = 5
        self.HandleToWaitDialog = None
        self.DialogText = 'Please Wait'
        self.DialogTitle = ''
        self.ProgressValue = 0
        self.Hold = False
        self.show_progressBar = False

    def __del__(self):
        self.hide()

    def show_and_hold(self, text='Please wait'):
        self.hide()
        self.DialogTitle = remove_html(text)
        self.DialogText = ''
        self.ProgressValue = 0
        self.Hold = True
        self._update()

    def hide(self):
        self.DialogTitle = 'Please wait'
        self.show_progressBar = False
        if self.HandleToWaitDialog:
            self.HandleToWaitDialog.close()
            del self.HandleToWaitDialog
            self.HandleToWaitDialog = None
        self.Hold = False

    def complete(self):
        """Call to complete a progress operation, which will also hide the
        dialog unless the dialog is being held"""

        self.show_progressBar = False
        self.ProgressValue = 100
        if not self.Hold:
            self.hide()
        else:
            self._update()

    def set_progress_text(self, text='Please wait'):
        self.DialogText = remove_html(text)
        self._update()

    def set_progress_value(self, progress_value):
        self.show_progressBar = True
        self._update()

        # Only call _update() when necessary
        if abs(progress_value - self.ProgressValue) >= self.IncrementThreshold:
            self.ProgressValue = progress_value
            self._update()

    def set_progress_and_message(self, progress_value, text):
        self.show_progressBar = True
        self.DialogText = remove_html(text)
        self.ProgressValue = progress_value
        self._update()

    def cancel_clicked(self):
        return False

    def resize(self, panel_position):
        pass

    def _update(self):
        text = self.DialogText or self.DialogTitle

        if self.HandleToWaitDialog:
            self.HandleToWaitDialog.update(self.ProgressValue)
            self.HandleToWaitDialog.set_description(text)
        else:
            self.HandleToWaitDialog = tqdm(total=100, desc=text,
                                           colour='green', leave=False)


@dataclass
class ProgressStackItem:
    """Used for handling a nested progress bar

    ProgressStackItem is part of the mechanism used to nest progress
    reporting, so that for example, if an operation is performed 4 times,
    the progress bar will not go from 0% to 100% 3 times, but instead go
    from 0% to 25% for the first operation, etc."""

    progress_text: str
    min_position: int
    max_position: int
    last_progress_value: int = 0
    visible: bool = False
