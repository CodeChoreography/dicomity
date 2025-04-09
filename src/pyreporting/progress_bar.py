from enum import Enum


class ProgressBar:
    """Interface for progress bar implementations"""

    def __init__(self, label: str = '', value: int = 0, title: str = '',
                 total: int = 100, parent = None):
        """Initialise progress bar

        Args:
            label: Text label in the progress bar
            value: Initial value of the progress bar
            title: The main heading in the progress bar, if there is one,
                   or the dialog title
            total: Maximum value of the progress bar
        """
        self.bar = None
        self.create(label=label, value=value, title=title, total=total,
                    parent=parent)

    def __del__(self):
        """Progress bar destructor"""
        self.close()

    def create(self, label: str = '', value: int = 0, title: str = '',
               total: int = 100, parent=None):
        """Create progress bar

        Args:
            label: Text label in the progress bar
            value: Initial value of the progress bar
            title: The main heading in the progress bar, if there is one,
                   or the dialog title
            total: Maximum value of the progress bar
            parent: Handle to parent window, when using a GUI interface
        """
        raise NotImplementedError

    def close(self):
        """Destroy progress bar"""
        raise NotImplementedError

    def update(self, label: str = None, value: int = None, title: str = None):
        """Update progress bar

        Args:
            label: If defined, change the text label for the progress bar
            value: If defined, change the progress completion value
            title: If defined, change the progress window title
        """
        raise NotImplementedError

    def cancel_clicked(self) -> bool:
        """Return True if the cancel button was clicked by the user"""
        raise NotImplementedError


class NoProgressBar(ProgressBar):
    """A do-nothing implementation of ProgressBar

    Used when you want to use the pyreporting Reporting class but don't
    actually want a visible progress bar"""

    def update(self, label: str = None, value: int = None, title: str = None,
               parent=None):
        pass

    def create(self, label: str = '', value: int = 0, title: str = '',
               total: int = 100, parent = None):
        pass

    def close(self):
        pass

    def cancel_clicked(self) -> bool:
        return False


class PySideProgressBar(ProgressBar):
    """A Pyside implementation of ProgressBar"""

    def create(self, label: str = '', value: int = 0, title: str = '',
               total: int = 100, parent=None):
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtGui import Qt
        self.bar = QProgressDialog(
            parent=parent,
            labelText=label,
            minimum=0,
            maximum=total
        )
        self.bar.setMinimumDuration(0)
        self.bar.setAutoReset(False)
        self.bar.setAutoClose(False)
        self.bar.setWindowModality(Qt.WindowModal)
        self.update(label=label, value=value, title=title)

    def close(self):
        if self.bar:
            self.bar.close()
            del self.bar
            self.bar = None

    def update(self, label: str = None, value: int = None, title: str = None):
        if label is not None:
            self.bar.setLabelText(label)
        if value is not None:
            self.bar.setValue(value)
        if title is not None:
            self.bar.setWindowTitle(title)

    def cancel_clicked(self) -> bool:
        return self.bar.wasCanceled()


class TerminalProgressBar(ProgressBar):
    """A terminal dialog used to report progress information using enlighten"""

    def create(self, label: str = '', value: int = 0,
               title: str = '', total: int = 100, parent=None):
        import enlighten
        manager = enlighten.get_manager()
        bar_format = '{desc}{desc_pad}{percentage:3.0f}%|{bar}|' \
                     ' {count:{len_total}d}/{total:d}'
        self.bar = manager.counter(
            total=total,
            desc=label,
            leave=False,
            bar_format=bar_format
        )
        self.update(label=label, value=value, title=title)

    def close(self):
        if self.bar:
            self.bar.close(clear=True)
            self.bar = None

    def update(self, label: str = None, value: int = None, title: str = None):
        if label is not None:
            self.bar.desc = label
        if value is not None:
            self.bar.count = value
        if value is not None or label is not None:
            self.bar.update(incr=0)

    def cancel_clicked(self):
        return False


class ProgressBarType(Enum):
    """Enum/factory for creating progress bars"""
    NONE = NoProgressBar
    QT = PySideProgressBar
    TERMINAL = TerminalProgressBar

    def make(self, **kwargs):
        return self.value(**kwargs)
