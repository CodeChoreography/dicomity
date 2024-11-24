from dataclasses import dataclass

from pyreporting.reporting import Reporting, ReportingDefault


class ReportingWithCache(Reporting):
    """Provides error, message and progress reporting, with
    warnings and messages cached to prevent display of duplicates
    
    ReportingWithCache is a wrapper around a Reporting object.
    Messages and warnings are cached using a ReportingWarningsCache and
    displayed at the end of the algorith. Duplicate messages and warnings are
    grouped together to prevent multiple messages appearing.
    
    See reporting.py for details of the methods this class implements.
    """
    def __init__(self, reporting=None):
        if not reporting:
            reporting = ReportingDefault()
        self._reporting = reporting
        self._warnings_cache = CoreReportingWarningsCache(self)

    def delete(self):
        self.showAndClearPendingMessages()
    
    def clearProgressStack(self):
        self._reporting.clearProgressStack()
    
    def pushProgress(self):
        self._reporting.pushProgress()

    def popProgress(self):
        self._reporting.popProgress()

    def log(self, identifier, message):
        self._reporting.logVerbose(identifier=identifier, message=message)

    def logVerbose(self, identifier, message):
        self._reporting.logVerbose(identifier=identifier, message=message)

    def showMessage(self, identifier, message, supplementary_info=None):
        self._warnings_cache.addPendingMessages(
            identifier, message, supplementary_info)

    def showMessageFromException(self, identifier, message, ex):
        self._reporting.showMessageFromException(identifier, message, ex)

    def showWarning(self, identifier, message, supplementary_info=None):
        self._warnings_cache.addPendingWarning(
            identifier, message, supplementary_info)

    def error(self, identifier, message):
        self._reporting.error(identifier, message)

    def errorFromException(self, identifier, message, ex):
        self._reporting.errorFromException(identifier, message, ex)

    def show_progress(self, text):
        self._reporting.show_progress(text)

    def completeProgress(self):
        self._reporting.completeProgress()

    def updateProgressMessage(self, text):
        self._reporting.updateProgressMessage(text)

    def updateProgressValue(self, progress_value):
        self._reporting.updateProgressValue(progress_value)

    def updateProgressAndMessage(self, progress_value, text):
        self._reporting.updateProgressAndMessage(progress_value, text)

    def updateProgressStage(self, progress_stage, num_stages):
        self._reporting.updateProgressStage(progress_stage, num_stages)

    def hasBeenCancelled(self):
        return self._reporting.hasBeenCancelled()

    def checkForCancel(self):
        self._reporting.checkForCancel()

    def showAndClearPendingMessages(self):
        self._warnings_cache.showAndClear()
        self._reporting.showAndClearPendingMessages()

    def showCachedMessage(self, identifier, message, supplementary_info):
        self._reporting.showMessage(identifier, message)

    def showCachedWarning(self, identifier, message, supplementary_info):
        self._reporting.showWarning(identifier, message, supplementary_info)

    def openPath(self, file_path, message):
        self._reporting.openPath(file_path, message)


@dataclass
class PendingRecord:
    ID: str
    Text: str
    SupplementaryInfo: str
    Count: int = 1


class CoreReportingWarningsCache:
    def __init__(self, reporting_with_cache):
        self._reporting_with_cache = reporting_with_cache
        self._pending_messages = {}
        self._pending_warnings = {}

    def addPendingWarning(self, warning_id, warning_text, supplementary_info):
        if warning_id in self._pending_warnings:
            self._pending_warnings[warning_id].Count += 1
        else:
            self._pending_warnings[warning_id] = PendingRecord(
                ID=warning_id,
                Text=warning_text,
                SupplementaryInfo=supplementary_info
            )

    def addPendingMessages(self, message_id, message_text, supplementary_info):
        if message_id in self._pending_messages:
            self._pending_messages[message_id].Count += 1
        else:
            self._pending_warnings[message_id] = PendingRecord(
                ID=message_id,
                Text=message_text,
                SupplementaryInfo=supplementary_info
            )

    def showAndClear(self):
        for warning_id, warning in self._pending_warnings.items():
            warning_text = warning.Text
            if warning.Count > 1:
                warning_text = f'(repeated x{warning.Count}) {warning.Text}'
            self._reporting_with_cache.showCachedWarning(
                identifier=warning_id,
                message=warning_text,
                supplementary_info=warning.SupplementaryInfo)
        self._pending_warnings.clear()

        for message_id, message in self._pending_messages.items():
            message_text = message.Text
            if message.Count > 1:
                message_text = f'(repeated x{message.Count}) {message.Text}'
            self._reporting_with_cache.showCachedMessage(
                identifier=message_id,
                message=message_text,
                supplementary_info=message.SupplementaryInfo)
        self._pending_messages.clear()