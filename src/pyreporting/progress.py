from dataclasses import dataclass
from pyreporting.progress_bar import ProgressBarType
from pyreporting.util import UserCancelled


class Progress:
    """Handler for a progress bar supporting nested progress reporting

    The Reporting class uses this interface to display and update a
    progress bar and associated text. The actual progress bar is created
    using a factory defined by the progress_type parameter (or type
    ProgressBarType) which allows for a terminal-based or PySide QT dialog,
    or you can implement your own custom ProgressBar class.
    """

    def __init__(self, progress_type: ProgressBarType, parent=None):
        self.progress_factory = progress_type
        self.stack = [ProgressStackItem(bar_min=0, bar_step=100)]
        self.progress_bar = None
        self.hold = False
        self.parent = parent

    def __del__(self):
        self.hide()

    def show(self, label='Please wait', value: int = 0, title: str = '',
             hold: bool = False):
        """Initialise progress dialog

        Args:
            label: Text to display in progress bar
            value: Current progress bar value, initialise at 0
            title: Title text for the progress dialog
            hold: set to True to keep progress visible until hide() is called
        """
        self.hold = hold
        self.update(label=label, value=value, title=title)

    def complete(self):
        """Indicates completion of progress, which will hide the progress bar
        unless it is being held, in which case it will set to 100%
        """
        if self.hold or len(self.stack) > 1:
            self.update(value=100)
        else:
            self.hide()

    def hide(self):
        """Hide the progress dialog"""
        self.hold = False
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None

    def update(self, value: int = None, step: int = None, label: str = None,
               title: str = None):
        """Update the label or value of the progress bar.

        Unspecified parameters for value, label or title will retain their
        previous value.

        If step is not specified, it will be computed automatically from the
        difference between previous value updates. The step is used with
        nested progress (push_progress and pop_progress) so that the range
        of the nested progress will run between value and value + step

        Args:
            value: The progress percentage
            step: Percentage difference between progress calls.
            label: The label text to display by the progress
            title: The title of the progress dialog
        """

        # Update values in the stack
        if step is None:
            if value is not None and value > self.stack[-1].value:
                self.stack[-1].step = value - self.stack[-1].value
        else:
            self.stack[-1].step = step

        if value is not None:
            self.stack[-1].value = value

        if label is not None:
            self.stack[-1].label = label

        if title is not None:
            self.stack[-1].title = title

        # Update existing progress bar or create a new one
        if self.progress_bar:
            self.progress_bar.update(
                label=self.stack[-1].label,
                value=self.stack[-1].global_progress(),
                title=self.stack[-1].title
            )
        else:
            self.progress_bar = self.progress_factory.make(
                parent=self.parent,
                label=self.stack[-1].label,
                value=self.stack[-1].global_progress(),
                title=self.stack[-1].title
            )
        self.check_for_cancel()

    def update_stage(self, stage: int, num_stages: int, label: str = None,
                     title: str = None):
        """Update the progress bar by specifying the number of stages to
        complete and the current stage being performed.

        Unspecified parameters for label or title will retain their
        previous value

        Args:
            stage: The index of the current stage
            num_stages: Total number of stages
            label: The label text to display by the progress
            title: The title of the progress dialog
        """

        value = round(100*stage/num_stages)
        step = round(100/num_stages)
        self.update(value=value, step=step, label=label, title=title)

    def has_been_cancelled(self) -> bool:
        """Return True if the user has clicked Cancel in the progress dialog"""
        if self.progress_bar:
            return self.progress_bar.cancel_clicked()
        else:
            return False

    def check_for_cancel(self):
        """Raise Cancel exception if user has clicked Cancel"""
        if self.has_been_cancelled():
            self.hide()
            self.clear_progress_stack()
            raise UserCancelled()

    def push(self):
        """Nest progress reporting. After calling this function, subsequent
        progress updates will modify the progress bar between the current
        value and the current value plus the last step
        """
        self.stack.append(ProgressStackItem(
            bar_min=self.stack[-1].global_progress(),
            bar_step=self.stack[-1].global_step(),
        ))

    def pop(self):
        """Remove one layer of nested progress nesting, returning to the
        previous progress reporting."""
        if len(self.stack) > 1:
            self.stack.pop()

    def clear_progress_stack(self):
        """Clear all progress nesting"""
        self.stack = [ProgressStackItem(bar_min=0, bar_step=100)]

    def set_progress_parent(self, parent):
        self.parent = parent


@dataclass
class ProgressStackItem:
    """Used for handling a nested progress bar

    ProgressStackItem is part of the mechanism used to nest progress
    reporting, so that for example, if an operation is performed 4 times,
    the progress bar will not go from 0% to 100% 3 times, but instead go
    from 0% to 25% for the first operation, etc."""

    bar_min: int
    bar_step: int
    label: str = ''
    title: str = ''
    value: int = 0
    step: int = 1

    def global_progress(self) -> int or None:
        return round(self.bar_min + self.value * self.bar_step / 100)

    def global_step(self) -> int or None:
        return round(self.step * self.bar_step / 100)
