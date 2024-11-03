"""Functions for reading DICOM files ith dicomity"""

from os.path import join
from typing import Optional

import numpy as np
from pydicom import filereader, FileDataset

from dicomity.dictionary import DicomDictionary
from dicomity.types import GroupingMetadata


def read_dicom_image(file_name: str) -> np.array:
    meta = filereader.dcmread(file_name, stop_before_pixels=False)
    return meta.pixel_array


def read_dicom_tags(
        file_name: str,
        dictionary: Optional[DicomDictionary] = None,
        specific_tags: Optional[list[str]] = None
) -> FileDataset:
    if dictionary:
        specific_tags = dictionary.allTags()
    meta = filereader.dcmread(
        file_name,
        stop_before_pixels=True,
        specific_tags=specific_tags
    )
    return meta


def read_grouping_metadata(file_name: str) -> GroupingMetadata:
    meta = filereader.dcmread(fp=file_name,
                              stop_before_pixels=True,
                              specific_tags=GroupingMetadata.groupingTags())
    return GroupingMetadata.fromPyDicom(meta)


def is_dicom(file_name: str) -> bool:
    """Test whether a file is in DICOM format

    Uses a simple test for the DICM preamble - this is very fast but
    may occasionally produce false positives.

    For a more robust guarantee that a file really is DICOM, first call this
    function and if True, try to parse the file - if the tag data cannot be
    parsed then it is likely not a DICOM file

    Args:
        file_name: path and filename of the file to test

    Returns:
        True if the file appears to be a Dicom file
    """

    with open(file_name, "rb") as f:
        f.seek(128)
        preamble = f.read(4)
        return preamble == b"DICM"


def is_dicom_image_file(file_path: str, file_name: str):
    """Tests if a file is a DICOM file but not a DICOMDIR file

    Args:
        file_path:
        file_name:

    Returns:
        True if the file is DICOM and not a DICOMDIR
    """
    if file_name == 'DICOMDIR':
        return False

    return is_dicom(join(file_path, file_name))
