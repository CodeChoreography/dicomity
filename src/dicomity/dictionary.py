from dicomity.types import TagDefinition


class DicomDictionary:
    """Build a dictionary for use with read_dicom_tags
        
    DicomDictionary can be used to construct a dictionary containing
    the Dicom tags you wish to read in using read_dicom_tags. A
    smaller subset of tags can reduce the time taken to parse a Dicom
    file.
        
    Usage:
        Several class methods provide useful dictionaries for most purposes:

         dictionary = DicomDictionary.grouping_dictionary()
             creates a dictionary of tags needed for grouping files
             together into volumes

         dictionary = DicomDictionary.essential_dictionary()
             creates a dictionary containing tags that are commonly used,
             including the pixel data

         dictionary = DicomDictionary.essential_dictionary_without_pixel_data()
             creates a dictionary containing tags that are commonly used,
             excluding the pixel data

         dictionary = DicomDictionary.complete_dictionary()
             creates a dictionary containing most public tags, including
             the pixel data
        
    """

    grouping_dictionary_without_pixel_data_singleton = None
    essential_dictionary_singleton = None
    essential_tags_dictionary_without_pixel_data_singleton = None
    complete_dictionary_singleton = None

    def __init__(self, tags):
        # The item delimiter is a special case. It must always be the
        # last tag in the list, so that the tag reading algorithm can
        # choose to ignore it
        tags.append(DicomDictionary._item_delimiter_tag())

        self.Dictionary = tags
        self._make_tag_list()
        self._make_tag_map()

    @classmethod
    def grouping_dictionary(cls):
        if not cls.grouping_dictionary_without_pixel_data_singleton:
            cls.grouping_dictionary_without_pixel_data_singleton = \
                DicomDictionary._create_grouping_tags_dictionary(
                    add_pixel_data=False)
        return cls.grouping_dictionary_without_pixel_data_singleton

    @classmethod
    def essential_dictionary(cls):
        if not cls.essential_dictionary_singleton:
            cls.essential_dictionary_singleton = \
                DicomDictionary._create_essential_tags_dictionary(
                    add_pixel_data=True)
        return cls.essential_dictionary_singleton

    @classmethod
    def essential_dictionary_without_pixel_data(cls):
        if not cls.essential_tags_dictionary_without_pixel_data_singleton:
            cls.essential_tags_dictionary_without_pixel_data_singleton \
                = DicomDictionary._create_essential_tags_dictionary(
                    add_pixel_data=False)
        return cls.essential_tags_dictionary_without_pixel_data_singleton

    @classmethod
    def complete_dictionary(cls):
        if not cls.complete_dictionary_singleton:
            cls.complete_dictionary_singleton = \
                DicomDictionary._create_all_tags_dictionary(add_pixel_data=True)
        return cls.complete_dictionary_singleton

    def _make_tag_list(self):
        self.tag_list = [d.TagIndex for d in self.Dictionary]

    def _make_tag_map(self):
        self.tag_map = {}
        for t in self.Dictionary:
            self.tag_map[t.TagIndex] = t

    @staticmethod
    def _create_grouping_tags_dictionary(add_pixel_data):
        tags = DicomDictionary._grouping_tags()
        if add_pixel_data:
            tags.append(DicomDictionary._pixel_data_tag())
        return DicomDictionary(tags)

    @staticmethod
    def _create_essential_tags_dictionary(add_pixel_data):
        tags = DicomDictionary._essentialTags()
        if add_pixel_data:
            tags.append(DicomDictionary._pixel_data_tag())
        return DicomDictionary(tags)

    @staticmethod
    def _create_all_tags_dictionary(add_pixel_data):
        tags = DicomDictionary.allTags()
        if add_pixel_data:
            tags.append(DicomDictionary._pixel_data_tag())
        return DicomDictionary(tags)

    @staticmethod
    def _pixel_data_tag():
        return TagDefinition('7FE0,0010', 'OB', 'PixelData')

    @staticmethod
    def _item_delimiter_tag():
        return TagDefinition('FFFE,E00D', 'UN', 'ItemDelimitationItem')

    @staticmethod
    def _grouping_tags():
        # pylint: disable=line-too-long
        tags = []
        tags.append(TagDefinition('0002,0000', 'UL', 'FileMetaInformationGroupLength'))
        tags.append(TagDefinition('0002,0010', 'UI', 'TransferSyntaxUID'))
        tags.append(TagDefinition('0008,0018', 'UI', 'SOPInstanceUID'))
        tags.append(TagDefinition('0008,0021', 'DA', 'SeriesDate'))
        tags.append(TagDefinition('0008,0031', 'TM', 'SeriesTime'))
        tags.append(TagDefinition('0008,0060', 'CS', 'Modality'))
        tags.append(TagDefinition('0008,1030', 'LO', 'StudyDescription'))
        tags.append(TagDefinition('0008,103E', 'LO', 'SeriesDescription'))
        tags.append(TagDefinition('0010,0010', 'PN', 'PatientName'))
        tags.append(TagDefinition('0010,0020', 'LO', 'PatientID'))
        tags.append(TagDefinition('0020,000D', 'UI', 'StudyInstanceUID'))
        tags.append(TagDefinition('0020,000E', 'UI', 'SeriesInstanceUID'))
        return tags

    @staticmethod
    def _essentialTags():
        # pylint: disable=line-too-long
        tags = []
        tags.append(TagDefinition('0002,0000', 'UL', 'FileMetaInformationGroupLength'))
        tags.append(TagDefinition('0002,0002', 'UI', 'MediaStorageSOPClassUID'))
        tags.append(TagDefinition('0002,0010', 'UI', 'TransferSyntaxUID'))
        tags.append(TagDefinition('0002,0012', 'UI', 'ImplementationClassUID'))

        tags.append(TagDefinition('0008,0008', 'CS', 'ImageType'))
        tags.append(TagDefinition('0008,0016', 'UI', 'SOPClassUID'))
        tags.append(TagDefinition('0008,0018', 'UI', 'SOPInstanceUID'))
        tags.append(TagDefinition('0008,0020', 'DA', 'StudyDate'))
        tags.append(TagDefinition('0008,0021', 'DA', 'SeriesDate'))
        tags.append(TagDefinition('0008,0060', 'CS', 'Modality'))
        tags.append(TagDefinition('0008,0070', 'LO', 'Manufacturer'))
        tags.append(TagDefinition('0008,1030', 'LO', 'StudyDescription'))
        tags.append(TagDefinition('0008,103E', 'LO', 'SeriesDescription'))

        tags.append(TagDefinition('0010,0010', 'PN', 'PatientName'))
        tags.append(TagDefinition('0010,0020', 'LO', 'PatientID'))
        tags.append(TagDefinition('0010,0030', 'DA', 'PatientsBirthDate'))

        tags.append(TagDefinition('0018,1250', 'SH', 'ReceiveCoilName'))

        tags.append(TagDefinition('0018,5100', 'CS', 'PatientPosition'))

        tags.append(TagDefinition('0020,000D', 'UI', 'StudyInstanceUID'))
        tags.append(TagDefinition('0020,000E', 'UI', 'SeriesInstanceUID'))
        tags.append(TagDefinition('0020,0010', 'SH', 'StudyID'))
        tags.append(TagDefinition('0020,0011', 'IS', 'SeriesNumber'))
        tags.append(TagDefinition('0020,0020', 'CS', 'PatientOrientation'))
        tags.append(TagDefinition('0020,0032', 'DS', 'ImagePositionPatient'))
        tags.append(TagDefinition('0020,0037', 'DS', 'ImageOrientationPatient'))
        tags.append(TagDefinition('0020,0052', 'UI', 'FrameOfReferenceUID'))
        tags.append(TagDefinition('0020,1002', 'IS', 'ImagesInAcquisition'))
        tags.append(TagDefinition('0020,1041', 'DS', 'SliceLocation'))

        tags.append(TagDefinition('0028,0002', 'US', 'SamplesPerPixel'))
        tags.append(TagDefinition('0028,0004', 'CS', 'PhotometricInterpretation'))
        tags.append(TagDefinition('0028,0006', 'US', 'PlanarConfiguration'))
        tags.append(TagDefinition('0028,0008', 'IS', 'NumberOfFrames'))
        tags.append(TagDefinition('0028,0010', 'US', 'Rows'))
        tags.append(TagDefinition('0028,0011', 'US', 'Columns'))
        tags.append(TagDefinition('0028,0030', 'DS', 'PixelSpacing'))
        tags.append(TagDefinition('0028,0100', 'US', 'BitsAllocated'))
        tags.append(TagDefinition('0028,0101', 'US', 'BitsStored'))
        tags.append(TagDefinition('0028,0102', 'US', 'HighBit'))
        tags.append(TagDefinition('0028,0103', 'US', 'PixelRepresentation'))
        tags.append(TagDefinition('0028,0120', 'SS', 'PixelPaddingValue'))
        tags.append(TagDefinition('0028,1050', 'DS', 'WindowCenter'))
        tags.append(TagDefinition('0028,1051', 'DS', 'WindowWidth'))
        tags.append(TagDefinition('0028,1052', 'DS', 'RescaleIntercept'))
        tags.append(TagDefinition('0028,1053', 'DS', 'RescaleSlope'))
        return tags
