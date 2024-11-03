"""Classes for grouping DICOM data using dicomity"""

from collections import UserList
from dataclasses import dataclass
from statistics import mode
from typing import Optional

import math
import numpy as np

from pyreporting.reporting import ReportingDefault
from dicomity.util import compare_main_tags, sort

from dicomity.types import GroupingMetadata


@dataclass
class DicomItem:
    """Stores data about a Dicom file"""

    filename: str
    metadata: GroupingMetadata


class DicomStack(UserList):
    """Store a set of Dicom metadata structures, corresponding
    to a coherent sequence of images

    Created by the DicomGrouper class, which separates and groups images into
    coherent sequences according to their metadata.
    """

    def add(self, filename: str, metadata: GroupingMetadata):
        """Add a new item to the DicomStack

        Args:
            filename: Dicom file name
            metadata: Dicom metadata
        """
        self.data.append(DicomItem(filename=filename, metadata=metadata))

    def matches(self, other_metadata: GroupingMetadata):
        """Determine if the DICOM file with the specified metadata belongs in
        this group

        Args:
            other_metadata: other file metadata to compare against this one

        Returns:
            True if the metadata should be part of this group
        """

        if len(self.data) < 1:
            raise ValueError("There are no images in this DicomStack")

        additional_image = self.data[1] if len(self.data) > 1 else None

        return are_images_groupable(
            self.data[0],
            other_metadata,
            additional_image
        )

    def sort_and_get_parameters(self, reporting):
        """Sorts the images according to slice location, and computes values for
        slice thickness and global origin"""
        sorted_indices, slice_thickness, global_origin_mm, sorted_positions = \
            self.sort_images_by_location(reporting)
        if len(self.data) > 1:
            if sorted_indices is None:
                reporting.show_warning(
                    id='DicomStack:UnableToSortFiles',
                    message='The images in this series may appear in the wrong '
                            'order because I was unable to determine the '
                            'correct ordering')
            else:
                self.data = [self.data[i] for i in sorted_indices]
        return slice_thickness, global_origin_mm, sorted_positions

    def sort_images_by_location(self, reporting=None):
        """Sort a series of Dicom images by their slice locations and calculate
        additional image parameters

        Args:
            reporting: - A CoreReporting or implementor of the same interface,
                for error and progress reporting.

        Returns:
            Tuple of:

            sorted_indices - The indices of the metadata structures in
                metadata_grouping, ordered by slice location

            slice_thickness - A typical slice thickness for this group of
                images

            global_origin_mm - The coordinates of the first voxel in the image
                volume

            sorted_positions - The ImagePositionPatient for
                each slice in the sorted

        """

        if not reporting:
            reporting = ReportingDefault()
        reporting.show_progress('Ordering images')
        reporting.update_progress_value(0)

        # Determine if ImagePositionPatient and SliceLocation tags exist.
        # It is sufficient to only check the metadata for one image, assuming
        # that the metadata was grouped prior to calling this function. The
        # grouping ensures that within a group, each of these tags exist for
        # either all or no images.
        representative_metadata = self.data[0].metadata
        if hasattr(representative_metadata, 'ImagePositionPatient'):
            image_positions_patient = [item.metadata.ImagePositionPatient
                                       for item in self.data]
        else:
            image_positions_patient = None

        if hasattr(representative_metadata, 'SliceLocation'):
            slice_locations = [item.metadata.SliceLocation
                               for item in self.data]
        else:
            slice_locations = None

        if hasattr(representative_metadata, 'InstanceNumber'):
            instance_numbers = [item.metadata.InstanceNumber
                                for item in self.data]
        else:
            instance_numbers = None

        # Try to calculate slice locations from the ImagePositionPatient tags
        if hasattr(representative_metadata, 'ImagePositionPatient'):

            # The first slice in the sequence may not be the actual first slice
            # in the image, but this does not matter
            first_slice_position = np.array(image_positions_patient[0])
            offset_positions = [np.array(item.metadata.ImagePositionPatient) -
                                first_slice_position for item in self.data]

            # Work out the relative direction of each slice relative to the
            # 'first' slice
            orientation_1 = np.array(
                representative_metadata.ImageOrientationPatient[0:3])
            orientation_2 = np.array(
                representative_metadata.ImageOrientationPatient[3:6])
            normal_vector = np.cross(orientation_1, orientation_2)
            # directions = [np.sign(np.dot(normal_vector, offset)) for offset in
            #                       offset_positions]

            # We compute the displacements of the image position, which assumes
            # the images form a cuboid stack. Really to compute the slice
            # spacing we should compute the distance of the image position to
            # the plane formed by the image orientation vectors
            image_slice_locations = [np.sign(np.dot(normal_vector, offset)) *
                                     math.sqrt(offset[0] ** 2 + offset[1] ** 2 +
                                               offset[2] ** 2) for offset
                                     in offset_positions]
            # image_slice_locations = directions.*sqrt(
            # offset_positions(:, 1).^2 + offset_positions(:, 2).^2 +
            # offset_positions(:, 3).^2)

            sorted_slice_locations, sorted_indices = sort(image_slice_locations)
            global_origin_mm = [
                min(p[0] for p in image_positions_patient),
                min(p[1] for p in image_positions_patient),
                min(p[2] for p in image_positions_patient)
            ]
            slice_thicknesses = [abs(sorted_slice_locations[i] -
                                     sorted_slice_locations[i - 1]) for i in
                                 range(1, len(sorted_slice_locations))]

        # If this tag is not present, we try the SliceLocation tags
        elif slice_locations:
            sorted_slice_locations, sorted_indices = sort(slice_locations)
            global_origin_mm = None
            slice_thicknesses = [abs(sorted_slice_locations[i] -
                                     sorted_slice_locations[i - 1]) for i in
                                 range(1, len(sorted_slice_locations))]

        # In the absense of the above tags, we sort by the instance number
        # (slice number). Ths is less reliable
        elif instance_numbers:
            _, sorted_indices = sort(instance_numbers)
            global_origin_mm = None
            slice_thicknesses = None

        # Otherwise, we set everything to empty
        else:
            sorted_indices = None
            global_origin_mm = None
            slice_thicknesses = None

        sorted_positions = None
        if image_positions_patient:
            sorted_positions = [image_positions_patient[i] for i in
                                sorted_indices]

        # Remove any zero thicknesses, which may indicate multiple slices at the
        # same position
        if slice_thicknesses and any(thickness < 0.01 for thickness in
                                     slice_thicknesses):
            reporting.show_warning(
                'sort_images_by_location:ZeroSliceThickness',
                'This image contains more than one image at the same slice '
                'position')
            slice_thicknesses = [thickness for thickness in slice_thicknesses
                                 if thickness > 0.01]

        # If we have no non-zero slice thicknesses (including the case where we
        # only have a single slice) then try and use the SliceThickness tag if
        # it exists. Otherwise, we just set to empty to indicate that we cannot
        # determine this
        if not slice_thicknesses:
            if hasattr(self.data[0], 'SliceThickness'):
                slice_thickness = self.data[0].SliceThickness
            else:
                slice_thickness = None
        else:
            slice_thickness = mode(slice_thicknesses)
            if any(thickness - slice_thickness > 0.01 for thickness in
                   slice_thicknesses):
                reporting.show_warning(
                    'sort_images_by_location:InconsistentSliceThickness',
                    'Not all slices have the same thickness')

        reporting.complete_progress()
        return sorted_indices, slice_thickness, global_origin_mm, \
            sorted_positions


class DicomGrouper(UserList):
    """Separate a series of Dicom images into groups of coherent images

    DicomGrouper splits a series of Dicom images into 'groups' of images with
    similar orientations and image properties. For example, a series containing
    a scout image will typically be separated into a group containing the scan
    images and another group containing the scout image. Similarly, a
    localizer series containing images in multiple orientations will typically
    be separated into a separate group for each orientation.
    """

    def add_item(self, filename: str, metadata: GroupingMetadata):
        """Add new metadata for an image. If the metadata is coherent with an
        existing group, add the image to that group. Otherwise, create a new
        group.

        Args:
            filename: path to image
            metadata: image metadata
        """

        self.find_stack(metadata).add(filename=filename, metadata=metadata)

    def number_of_groups(self) -> int:
        """Return the number of groups in this data"""
        return len(self.data)

    def get_stack(self, index: int) -> DicomStack:
        """Return a particular DicomStack"""
        return self.data[index]

    def largest_stack(self) -> Optional[DicomStack]:
        """Return the stack with the greatest number of images"""

        if len(self.data) < 1:
            return None

        return max(self.data, key=lambda g: len(g))

    def find_stack(self, metadata: GroupingMetadata) -> DicomStack:
        """Find a stack to which the specified image metadata can be added

        Searches for a DicomStack to which the new image metadata could be
        added while forming a coherent image set. If no existing group exists,
        create and return a new empty group

        Args:
            metadata: image metadata

        Returns:
            The DicomStack to which the image metadata belongs, or a new group
        """
        for grouping in self.data:
            if grouping.matches(metadata):
                return grouping
        return DicomStack()


def are_images_groupable(
        this_metadata: GroupingMetadata,
        other_metadata: GroupingMetadata,
        additional_metadata: Optional[GroupingMetadata] = None
):
    """Determine whether two Dicom images form a coherent sequence

    Compares the metadata from two Dicom images. If the images are from the same
    patient, study and series, and have similar orientations, data types and
    image types, then they are considered to be part of a coherent sequence.

    Args:
        this_metadata: metadata for the image being tested
        other_metadata: metadata for existing image in group
        additional_metadata: metadata for additional image. This is only used
            for checking that the image locations form a coherent set. Set to
            None if there are currently no other images in the group

    Returns:
        True if the images form a coherent sequence
    """

    # Check that the main Dicom tags match
    match = compare_main_tags(this_metadata, other_metadata)

    # Check that image coordinates lie in a straight line
    if additional_metadata is not None:
        match = match and compare_main_tags(additional_metadata, other_metadata)
        match = match and are_image_locations_consistent(
            this_metadata, other_metadata, additional_metadata)
    return match


def are_image_locations_consistent(
        first_metadata: GroupingMetadata,
        second_metadata: GroupingMetadata,
        third_metadata: GroupingMetadata,
        tolerance_mm: float = 10):
    """Determine if three Dicom images are parallel and lie approximately on
    a straight line, i.e. they form a volume

    Args:
        first_metadata: metadata of image 1
        second_metadata: metadata of image 2
        third_metadata: metadata of image 3
        tolerance_mm: maximum permitted absolute difference between each
            component of the normalised vectors

    Returns:
        True if three images lie approximately on a straight line
        (determined by the coordinates in the ImagePositionPatient Dicom tags)
    """

    # If the ImagePositionPatient tag is not present, assume the images are
    # consistent
    if (not hasattr(first_metadata, 'ImagePositionPatient')) and \
            (not hasattr(second_metadata, 'ImagePositionPatient')) and \
            (not hasattr(third_metadata, 'ImagePositionPatient')):
        return True

    # First get the image position
    first_position = np.array(first_metadata.ImagePositionPatient)
    second_position = np.array(second_metadata.ImagePositionPatient)
    third_position = np.array(third_metadata.ImagePositionPatient)

    # Next, compute direction vectors between the points
    direction_vec_1 = second_position - first_position
    direction_vec_2 = third_position - first_position

    # Find a scaling between the direction vectors
    scale_index_1 = np.argmax(np.abs(direction_vec_1))
    max_1 = np.abs(direction_vec_1)[scale_index_1]
    scale_index_2 = np.argmax(np.abs(direction_vec_2))
    max_2 = np.abs(direction_vec_2)[scale_index_2]

    if max_1 > max_2:
        scale_1 = 1
        scale_2 = direction_vec_1[scale_index_2]/direction_vec_2[scale_index_2]
    else:
        scale_1 = direction_vec_2[scale_index_1]/direction_vec_1[scale_index_1]
        scale_2 = 1

    # Scale
    scaled_direction_vector_1 = direction_vec_1*scale_1
    scaled_direction_vector_2 = direction_vec_2*scale_2

    # Find the maximum absolute difference between the normalised vectors
    difference = np.abs(scaled_direction_vector_2 - scaled_direction_vector_1)
    max_difference = np.amax(difference)

    return max_difference <= tolerance_mm
