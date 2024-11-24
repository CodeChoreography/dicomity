from dataclasses import dataclass
from os.path import join

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class CoreFilename:
    """A structure for holding a file name and path"""

    file_path: str = None
    file_name: str = None

    def fullFile(self):
        return join(self.file_path, self.file_name)
