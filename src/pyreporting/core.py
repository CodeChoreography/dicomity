class CoreException(Exception):
    def __init__(self, message, identifier=None):
        super().__init__(message)
        self.identifier = id

APP_NAME = "pyreporting"
APP_AUTHOR = "CodeChoreography"