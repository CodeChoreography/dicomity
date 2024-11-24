"""Utility functions for dicomity"""
import re
from datetime import datetime

import numpy as np
from natsort import natsorted
from appdirs import user_config_dir

from dicomity.types import GroupingMetadata, PatientName
from pyreporting.core import APP_NAME, APP_AUTHOR


def compare_inexact(
        field_name: str,
        this_metadata,
        other_metadata,
        tolerance
):
    """Compare numerical attributes with a tolerance

    The attributes do not have to exist, but they must both exist or both not
    exist for a True match

    Args:
        field_name:
        this_metadata:
        other_metadata:
        tolerance:

    Returns:

    """

    # If this field does not exist in either metadata, then return a
    # true match
    if not hasattr(this_metadata, field_name) and not \
            hasattr(other_metadata, field_name):
        return True

    # If this field exists in one but not the other, return a false
    # match
    if hasattr(this_metadata, field_name) != \
            hasattr(other_metadata, field_name):
        return False

    # Get the values of this field
    field_this = getattr(this_metadata, field_name)
    field_other = getattr(other_metadata, field_name)

    # If the field values are of a different type, return a false match
    if not isinstance(field_this, type(field_other)):
        return False

    # Inexact numeric match
    return np.amax(np.abs(np.subtract(field_this, field_other))) < tolerance


# pylint: disable-next=too-many-return-statements
def compare_main_tags(
        this_metadata: GroupingMetadata,
        other_metadata: GroupingMetadata
):
    """

    Args:
        this_metadata: Metadata for first file
        other_metadata:  Metadata for second file

    Returns:
        True if the fields match. False if any fields no not match. False if
            any field exists in only one of the metadata
    """

    # Check for exact matches in certain fields
    fields_to_compare = [
        'PatientName', 'PatientID', 'PatientBirthDate', 'StudyInstanceUID',
        'SeriesInstanceUID', 'StudyID', 'StudyDescription', 'SeriesNumber',
        'SeriesDescription', 'StudyDate', 'SeriesDate', 'Rows', 'Columns',
        'PixelSpacing', 'PatientPosition', 'FrameOfReferenceUID', 'Modality',
        'MediaStorageSOPClassUID', 'ImageType', 'SOPClassUID',
        'ImplementationClassUID', 'ImagesInAcquisition', 'SamplesPerPixel',
        'PhotometricInterpretation', 'BitsAllocated', 'BitsStored', 'HighBit',
        'PixelRepresentation'
    ]

    fields_to_compare = [field for field in fields_to_compare if
                         hasattr(this_metadata, field)]
    fields_to_compare_other = [field for field in fields_to_compare if
                               hasattr(other_metadata, field)]

    # Fields should exist in both metadata or neither
    if fields_to_compare != fields_to_compare_other:
        return False

    for field_name in fields_to_compare:
        if getattr(this_metadata, field_name) != \
                getattr(other_metadata, field_name):
            return False

    if not compare_inexact('ImageOrientationPatient', this_metadata,
                           other_metadata, 0.5):
        return False

    # Verify that the images contain the same tags relating to slice location
    if hasattr(this_metadata, 'SliceLocation') != \
            hasattr(other_metadata, 'SliceLocation'):
        return False

    if hasattr(this_metadata, 'ImagePositionPatient') != \
            hasattr(other_metadata, 'ImagePositionPatient'):
        return False

    if hasattr(this_metadata, 'ImagePositionPatient') != \
            hasattr(other_metadata, 'ImagePositionPatient'):
        return False

    # If the positions match exactly, then these are should not be in the
    # same group - they may be duplicates, or different time points
    if hasattr(this_metadata, 'ImagePositionPatient') and \
            hasattr(other_metadata, 'ImagePositionPatient') \
            and compare_inexact('ImagePositionPatient', this_metadata,
                                other_metadata, 0.0001):
        return False

    return True


def add_optional_field(text, struct_name, field_name, only_if_nonempty):
    """

    Args:
        text:
        struct_name:
        field_name:
        only_if_nonempty:

    Returns:

    """
    if text and only_if_nonempty:
        return text
    return ", ".join(filter(None,
                            [text, getattr(struct_name, field_name, None)]))


def patient_name_to_strings(patient_name: 'PatientName' or str):
    """Return string representations of patient name

    A Dicom PatientName may contain multiple fields. This function
    performs a simple combination of fields to produce a patient name
    string, and also a short version using the first field that is found

    Args:
        patient_name: Patient name as a str or PatientName

    Returns:
        Tuple containing
            Patient name as a str
            Short version of patient name as a str

    """
    if isinstance(patient_name, str):
        return patient_name, patient_name
    if not isinstance(patient_name, PatientName):
        return "", ""

    name = ''
    short_name = ''

    name = add_optional_field(name, patient_name, 'FamilyName', False)
    name = add_optional_field(name, patient_name, 'GivenName', False)
    name = add_optional_field(name, patient_name, 'MiddleName', False)
    name = add_optional_field(name, patient_name, 'NamePrefix', False)
    name = add_optional_field(name, patient_name, 'NameSuffix', False)

    short_name = add_optional_field(short_name, patient_name, 'FamilyName',
                                    True)
    short_name = add_optional_field(short_name, patient_name, 'GivenName',
                                    True)
    short_name = add_optional_field(short_name, patient_name, 'MiddleName',
                                    True)
    short_name = add_optional_field(short_name, patient_name, 'NamePrefix',
                                    True)
    short_name = add_optional_field(short_name, patient_name, 'NameSuffix',
                                    True)
    return name, short_name


def sort(array):
    """Sort array, return sorted values and sorted indices

    Args:
        array: array to sort

    Returns:
        Tuple of sorted values, sorted indices
    """
    array = np.array(array)
    sorted_indices = np.argsort(array)
    sorted_values = array[sorted_indices]
    return sorted_values, sorted_indices


def sort_filenames(original_filenames):
    """Sorts a list of filenames, taking into account numbers"""
    if len(original_filenames) > 0 and isinstance(original_filenames[0], CoreFilename):
        return natsorted(original_filenames, key=lambda cf: cf.fullFile())
    else:
        return natsorted(original_filenames)


def remove_html(html_text):
    """Strips out simple HTML tags from the provided string.
    Not suitable for sanitising untrusted strings"""
    text = re.sub('<[^<]+?>', ' ', html_text)
    return re.sub(' +', ' ', text)


def current_date_string():
    return datetime.now().strftime("%d-%b-%Y").upper()


def get_user_directory():
    """Returns path to the user's home folder"""
    return user_config_dir(APP_NAME, APP_AUTHOR)
