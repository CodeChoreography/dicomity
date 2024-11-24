import numpy as np

from dicomity.group import DicomGrouper
from dicomity.group import DicomStack


def test_grouper():
    grouper = DicomGrouper()
    assert grouper.largest_stack() == None
    # grouper.add_item()


def test_sort_images_by_location():
    group = DicomStack()
    group.add(filename="1", metadata=meta({'ImagePositionPatient': [0, 0, 1], 'ImageOrientationPatient': [1, 0, 0, 0, 1, 0]}))

    # grouping.append()
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [0])
    assert np.array_equal(sorted_positions, [[0, 0, 1]])
    assert slice_thickness == None
    assert global_origin_mm == [0, 0, 1]

    group.add(filename="2", metadata=meta({'ImagePositionPatient': [0, 0, 0], 'ImageOrientationPatient': [1, 0, 0, 0, 1, 0]}))
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [1, 0])
    assert np.array_equal(sorted_positions, [[0, 0, 0], [0, 0, 1]])
    assert slice_thickness == 1.0
    assert global_origin_mm == [0, 0, 0]

    group.add(filename="3", metadata=meta({'ImagePositionPatient': [0, 0, 2], 'ImageOrientationPatient': [1, 0, 0, 0, 1, 0]}))
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [1, 0, 2])
    assert np.array_equal(sorted_positions, [[0, 0, 0], [0, 0, 1], [0, 0, 2]])
    assert slice_thickness == 1.0
    assert global_origin_mm == [0, 0, 0]


def test_sort_images_by_instance():
    group = DicomStack()
    group.add(filename="1", metadata=meta({'InstanceNumber': 2}))
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [0])
    group.add(filename="2", metadata=meta({'InstanceNumber': 3}))
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [0, 1])
    group.add(filename="3", metadata=meta({'InstanceNumber': 1}))
    sorted_indices, slice_thickness, global_origin_mm, sorted_positions = group.sort_images_by_location()
    assert np.array_equal(sorted_indices, [2, 0, 1])


class DummyMeta:
    pass


def meta(din: dict):
    d = DummyMeta()
    for key, value in din.items():
        setattr(d, key, value)
    return d
