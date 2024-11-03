"""Custom classes for grouping DICOM files with dicomity"""

from dataclasses import dataclass, fields
from typing import Optional

from dataclasses_json import dataclass_json
from pydicom import FileDataset
from pydicom.multival import MultiValue
from pydicom.valuerep import PersonName


@dataclass_json
@dataclass
class GroupingMetadata:
    # pylint: disable=invalid-name
    """Store tags for an individual DICOM file used for grouping

    These are the tags used to group a set of Dicom Files into sets of coherent
    images
    """

    FileMetaInformationGroupLength: Optional[int] = None
    MediaStorageSOPClassUID: Optional[str] = None
    TransferSyntaxUID: Optional[str] = None
    ImplementationClassUID: Optional[str] = None
    ImageType: Optional[list[str]] = None

    SOPClassUID: Optional[str] = None
    SOPInstanceUID: Optional[str] = None
    StudyDate: Optional[str] = None
    SeriesDate: Optional[str] = None
    Modality: Optional[str] = None
    Manufacturer: Optional[str] = None
    StudyDescription: Optional[str] = None
    SeriesDescription: Optional[str] = None
    PatientName: Optional[PatientName] = None
    PatientID: Optional[str] = None
    PatientBirthDate: Optional[str] = None
    ReceiveCoilName: Optional[str] = None
    PatientPosition: Optional[str] = None
    StudyInstanceUID: Optional[str] = None
    SeriesInstanceUID: Optional[str] = None
    StudyID: Optional[str] = ''
    SeriesNumber: Optional[int] = ''
    PatientOrientation: Optional[str] = None
    ImagePositionPatient: Optional[list[float]] = None
    ImageOrientationPatient: Optional[list[float]] = None
    FrameOfReferenceUID: Optional[str] = None
    ImagesInAcquisition: Optional[int] = None
    SliceLocation: Optional[float] = None
    SamplesPerPixel: Optional[int] = None
    PhotometricInterpretation: Optional[str] = None
    PlanarConfiguration: Optional[int] = None
    NumberOfFrames: Optional[int] = None
    Rows: Optional[int] = None
    Columns: Optional[int] = None
    PixelSpacing: Optional[list[float]] = None
    BitsAllocated: Optional[int] = None
    BitsStored: Optional[int] = None
    HighBit: Optional[int] = None
    PixelRepresentation: Optional[int] = None
    PixelPaddingValue: Optional[int] = None
    WindowCenter: Optional[list[float]] = None
    WindowWidth: Optional[list[float]] = None
    RescaleIntercept: Optional[float] = None
    RescaleSlope: Optional[float] = None

    @staticmethod
    def groupingTags() -> list[str]:
        return [f.name for f in fields(GroupingMetadata)]

    @staticmethod
    def fromPyDicom(pydicom_meta: FileDataset):
        meta_data = GroupingMetadata()
        for tag in GroupingMetadata.groupingTags():
            meta_data._setOptionalTag(meta=pydicom_meta, tag=tag)
        meta_data.filename = pydicom_meta.filename
        return meta_data

    def _setOptionalTag(self, meta: FileDataset, tag: str):
        value = getattr(meta, tag, None)
        setattr(self, tag, GroupingMetadata.convert(value))

    @staticmethod
    def convert(value):
        if type(value) in [str, int, float, type(None)]:
            # Exact native types don't need to be converted
            return value
        if isinstance(value, int):
            # Convert pydicom int subclasses to int
            return int(value)
        elif isinstance(value, str):
            # Convert pydicom str subclasses to str
            return str(value)
        elif isinstance(value, float):
            # Convert pydicom float subclasses to float
            return float(value)
        elif isinstance(value, MultiValue):
            # Convert MultiValue to python list
            return [GroupingMetadata.convert(v) for v in value]
        elif isinstance(value, PersonName):
            # Convert special PatientName object
            return PatientName.from_pydicom(value)
        else:
            raise ValueError(f'GroupingMetadata does not currently support '
                             f'type {type(value).__name__} ')


class TagDefinition:
    """Used in creating a DicomDictionary"""

    def __init__(self, tag_string, vr_type, name):
        self.TagString = tag_string
        self.Tag = [int(tag_string[0:4], 16), int(tag_string[5:9], 16)]
        self.TagIndex = int(tag_string[0:4] + tag_string[5:9], 16)
        self.VRType = vr_type
        self.Name = name


@dataclass_json
@dataclass
class PatientName:
    FamilyName: str = ''
    GivenName: str = ''
    MiddleName: str = ''
    NamePrefix: str = ''
    NameSuffix: str = ''

    @staticmethod
    def from_pydicom(person_name: PersonName):
        return PatientName(
            FamilyName=person_name.family_name,
            GivenName=person_name.given_name,
            MiddleName=person_name.middle_name,
            NamePrefix=person_name.name_prefix,
            NameSuffix=person_name.name_suffix,
        )
