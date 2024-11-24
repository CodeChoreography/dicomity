"""Functions for loading an image volume from DICOM files"""

from os.path import join

import numpy as np

from dicomity.core import CoreFilename
from dicomity.util import sort_filenames
from pyreporting.reporting import ReportingDefault
from dicomity.dictionary import DicomDictionary
from dicomity.dicom import is_dicom, read_grouping_metadata, read_dicom_image
from dicomity.group import DicomGrouper, DicomStack


def load_main_image_from_dicom_files(image_path, filenames, reporting=None):
    """Loads a series of DICOM files into a coherent 3D volume

    Args:
        image_path: location of the DICOM files to load
        filenames:
        reporting: (Optional) An object implementing
            Reporting for error, warning
            and progress reporting. If no object is
            provided then a default reporting object
            is created.

    Returns:
        Tuple of: image_wrapper, representative_metadata, slice_thickness,
            global_origin_mm, sorted_positions

        image: a np.array containing the 3D volume
        representative_metadata: metadata from one slice of the main group
        slice_thickness: the computed distance between centrepoints of each
            slice
        global_origin_mm: The mm coordinates of the image origin
        sorted_positions: Patient positions for each slice in the sorted order
    """

    if not reporting:
        reporting = ReportingDefault()

    # A single filename can be specified as a string
    if isinstance(filenames, str):
        filenames = [filenames]

    # Load the metadata from the DICOM images, and group into coherent sequences
    file_grouper = load_metadata_from_dicom_files(image_path, filenames,
                                                  reporting)

    # Warn the user if we found more than one group, since the others will not
    # be loaded into the image volume
    if file_grouper.number_of_groups() > 1:
        reporting.show_warning(
            'load_main_image_from_dicom_files:MultipleGroupings',
            'I have removed some images from this dataset because the images '
            'did not form a coherent set. This may be due to the presence of '
            'scout images or dose reports, or localizer images in multiple '
            'orientations. I have formed a volume form the largest coherent '
            'set of images in the same orientation.')

    # Choose the group with the most images
    main_group = file_grouper.largest_stack()

    # Sort the images into the correct order
    slice_thickness, global_origin_mm, sorted_positions = \
        main_group.sort_and_get_parameters(reporting)

    # Obtain a representative set of metadata tags from the first image in the
    # sequence
    representative_metadata = main_group.metadata[0]

    # Load the pixel data
    image_volume = load_images_from_stack(
        stack=main_group,
        reporting=reporting
    )

    return image_volume, representative_metadata, slice_thickness, \
        global_origin_mm, sorted_positions


def load_metadata_from_dicom_files(image_path, filenames,
                                   reporting=None) -> DicomGrouper:
    """Load metadata from a series of DICOM files

    Args:
        image_path: specify the location of the DICOM files.
        filenames: filenames can be a string for a single filename, or an
            array of strings
        reporting: A CoreReporting or implementor of the same interface,
            for error and progress reporting. Create a CoreReporting
            with no arguments to hide all reporting. If no
            reporting object is specified then a default
            reporting object with progress dialog is
            created

    Returns:
        a DicomGrouper object containing the metadata grouped into coherent
            sequences of images
    """

    if not reporting:
        reporting = ReportingDefault()

    # Show progress dialog
    reporting.show_progress('Reading image metadata')
    reporting.update_progress_value(0)

    # A single filename can be specified as a string or CoreFilename
    if isinstance(filenames, str):
        filenames = [filenames]
    if isinstance(filenames, CoreFilename):
        filenames = [filenames]

    # Sort the filenames into numerical order. Normally, this ordering will be
    # overruled by the ImagePositionPatient or SliceLocation tags, but in the
    # absence of other information, the numerical slice ordering will be used.
    sorted_filenames = sort_filenames(filenames)
    num_slices = len(filenames)

    # The file grouper performs the sorting of image metadata
    dicom_grouper = DicomGrouper()

    dictionary = DicomDictionary.essential_dictionary_without_pixel_data()

    file_index = 0
    for next_file in sorted_filenames:
        if isinstance(next_file, CoreFilename):
            file_path = next_file.file_path
            file_name = next_file.file_name
        else:
            file_path = image_path
            file_name = next_file

        combined_file_name = join(file_path, file_name)
        if is_dicom(combined_file_name):
            dicom_grouper.add_item(
                filename=combined_file_name,
                metadata=read_grouping_metadata(combined_file_name))
        else:
            # If not a Dicom image, exclude it from the set and warn user
            reporting.show_warning(
                'load_metadata_from_dicom_files:NotADicomFile',
                f'load_metadata_from_dicom_files: The file '
                f'{combined_file_name} is not a DICOM file and will be '
                f'removed from this series.')

        reporting.update_progress_value(round(100 * file_index / num_slices))

        file_index += 1

    reporting.complete_progress()
    return dicom_grouper


def load_images_from_stack(stack: DicomStack, reporting=None) -> np.array:
    """Load metadata from a series of DICOM files

    Args:
        stack: a DicomStack containing metadata

        reporting: (Optional) A Reporting or other implementor of
            Reporting, for error and progress reporting.
            Create a Reporting with no arguments to hide all reporting. If
            no reporting object is specified then a default
            reporting object with progress dialog is
            created

    Returns:
        a numpy array object containing the image volume
    """

    if not reporting:
        reporting = ReportingDefault()

    reporting.show_progress('Reading pixel data')
    reporting.update_progress_value(0)

    num_slices = len(stack)

    # Load image slice
    first_image_slice = read_dicom_image(file_name=stack[0].filename)
    if first_image_slice is None:
        return np.array([])

    # Pre-allocate image matrix
    size_i = stack[0].metadata.Rows
    size_j = stack[0].metadata.Columns
    size_k = num_slices
    samples_per_pixel = stack[0].metadata.SamplesPerPixel

    # Pre-allocate image matrix
    data_type = first_image_slice.dtype
    if data_type == np.char:
        reporting.show_message(
            'load_images_from_stack:SettingDatatypeToInt8',
            'Char datatype detected. Setting to int8')
        data_type = 'int8'
    image_size = [size_i, size_j, size_k, samples_per_pixel] if \
        samples_per_pixel > 1 else [size_i, size_j, size_k]
    raw_image = np.zeros(image_size, data_type)
    if samples_per_pixel > 1:
        raw_image[:, :, 0, :] = first_image_slice
    else:
        raw_image[:, :, 0] = first_image_slice

    for file_index in range(1, num_slices):
        next_slice = read_dicom_image(file_name=stack[file_index].filename)
        if samples_per_pixel > 1:
            raw_image[:, :, file_index, :] = next_slice
        else:
            raw_image[:, :, file_index] = next_slice
        reporting.update_progress_value(round(100 * file_index / num_slices))

    reporting.complete_progress()
    return raw_image
