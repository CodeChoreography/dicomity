"""Functions for loading an image volume from DICOM files"""

import numpy as np

from pyreporting.reporting import get_reporting
from dicomity.util import sort_filenames
from dicomity.dictionary import DicomDictionary
from dicomity.dicom import is_dicom, read_grouping_metadata, read_dicom_image
from dicomity.group import DicomGrouper, DicomStack


def load_main_image_from_dicom_files(filenames: str or list[str]):
    """Loads a series of DICOM files into a coherent 3D volume

    Args:
        filenames: filepath or list of filepaths

    Returns:
        Tuple of: image, representative_metadata, slice_thickness,
            global_origin_mm, sorted_positions

        image: a numpy array containing the 3D volume
        representative_metadata: metadata from one slice of the main group
        slice_thickness: the computed distance between centrepoints of each
            slice
        global_origin_mm: The mm coordinates of the image origin
        sorted_positions: Patient positions for each slice in the sorted order
    """

    reporting = get_reporting()

    # A single filename can be specified as a string
    if isinstance(filenames, str):
        filenames = [filenames]

    # Load the metadata from the DICOM images, and group into coherent sequences
    file_grouper = load_metadata_from_dicom_files(filenames=filenames)

    if file_grouper.number_of_groups() < 1:
        return None, None, None, None, None

    # Warn the user if we found more than one group, since the others will not
    # be loaded into the image volume
    if file_grouper.number_of_groups() > 1:
        reporting.warning(
            identifier='load_main_image_from_dicom_files:MultipleGroupings',
            message='I have removed some images from this dataset because the '
                    'images did not form a coherent set. This may be due to '
                    'the presence of scout images or dose reports, or '
                    'localizer images in multiple orientations. I have formed '
                    'a volume form the largest coherent set of images in the '
                    'same orientation.')

    # Choose the group with the most images
    main_group = file_grouper.largest_stack()

    # Sort the images into the correct order
    slice_thickness, global_origin_mm, sorted_positions = \
        main_group.sort_and_get_parameters()

    # Obtain a representative set of metadata tags from the first image in the
    # sequence
    representative_metadata = main_group[0].metadata

    # Load the pixel data
    image = load_images_from_stack(stack=main_group)

    return image, representative_metadata, slice_thickness, \
        global_origin_mm, sorted_positions


def load_metadata_from_dicom_files(filenames: str or list[str]) -> DicomGrouper:
    """Load metadata from a series of DICOM files

    Args:
        filenames: filenames can be a string for a single filename, or an
            array of strings

    Returns:
        a DicomGrouper object containing the metadata grouped into coherent
            sequences of images
    """

    # Get the default pyreporting object
    reporting = get_reporting()

    # Show progress dialog
    reporting.start_progress(label='Reading image metadata', value=0)

    # A single filename can be specified as a string
    if isinstance(filenames, str):
        filenames = [filenames]

    # Sort the filenames into numerical order. Normally, this ordering will be
    # overruled by the ImagePositionPatient or SliceLocation tags, but in the
    # absence of other information, the numerical slice ordering will be used.
    sorted_filenames = sort_filenames(filenames)
    num_slices = len(filenames)

    # The DicomGrouper performs the sorting of image metadata
    dicom_grouper = DicomGrouper()

    dictionary = DicomDictionary.essential_dictionary_without_pixel_data()

    file_index = 0
    for next_file in sorted_filenames:
        file_name = next_file

        combined_file_name = file_name
        if is_dicom(combined_file_name):
            dicom_grouper.add_item(
                filename=combined_file_name,
                metadata=read_grouping_metadata(combined_file_name))
        else:
            # If not a Dicom image, exclude it from the set and warn user
            reporting.warning(
                identifier='load_metadata_from_dicom_files:NotADicomFile',
                message=f'load_metadata_from_dicom_files: The file '
                f'{combined_file_name} is not a DICOM file and will be '
                f'removed from this series.')

        reporting.update_progress(value=round(100 * file_index / num_slices))

        file_index += 1

    reporting.complete_progress()
    return dicom_grouper


def load_images_from_stack(stack: DicomStack) -> np.array:
    """Load metadata from a series of DICOM files

    Args:
        stack: a DicomStack containing metadata

    Returns:
        a numpy array containing the image volume
    """

    # Get the default pyreporting object
    reporting = get_reporting()

    reporting.start_progress(label='Reading pixel data', value=0)

    num_slices = len(stack)

    # Load image slice
    first_image_slice = read_dicom_image(file_name=stack[0].filename)
    if first_image_slice is None:
        return None

    # Pre-allocate image matrix
    size_i = stack[0].metadata.Rows
    size_j = stack[0].metadata.Columns
    size_k = num_slices
    samples_per_pixel = stack[0].metadata.SamplesPerPixel

    # Pre-allocate image matrix
    data_type = first_image_slice.dtype
    if data_type == np.char:
        reporting.info(
            identifier='load_images_from_stack:SettingDatatypeToInt8',
            message='Char datatype detected. Setting to int8')
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
        reporting.update_progress(value=round(100 * file_index / num_slices))

    reporting.complete_progress()
    return raw_image
