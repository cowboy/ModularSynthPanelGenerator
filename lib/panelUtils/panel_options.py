import adsk.core, adsk.fusion
from ..generalUtils.persist_utils import Persistable
from .. import fusionAddInUtils as futil

app = adsk.core.Application.get()

# All numeric values are in cm, which is the default for the Fusion API

class PanelOptions(Persistable):
  __anchorPoints = {
    f"{prefix.lower()}-{suffix.lower()}": "Center" if prefix == "Middle" and suffix == "Center" else f"{prefix} {suffix}"
    for prefix in ["Top", "Middle", "Bottom"]
    for suffix in ["Left", "Center", "Right"]
  }
  
  __supportTypes = {
    "none": "No reinforcements",
    "solid": "Solid (good for larger blanks)",
    "shell": "Shell (leaves space for components)",
  }
  __formatData = {
    "__defaults": {
      "hpWidth": 0.508,
      "slotDiameter": 0.35,
      "slotLength": 0.14,
      "slotOffsetY": 0.3,
      "slotOffsetX": 0.6,
    },
    "3u_eurorack": {
      "name": "3U Eurorack",
      "panelLength": 12.85,
      "maxPcbLength": 11.0,
    },
    "1u_intellijel": {
      "name": "1U (Intellijel)",
      "panelLength": 3.965,
      "maxPcbLength": 2.25,
    },
    "1u_pulplogic": {
      "name": "1U Tile (Pulp Logic)",
      "panelLength": 4.318,
      "maxPcbLength": 2.87,
      "slotOffsetX": 0.433,
    },
  }

  def __init__(self, persistFile: str):
    Persistable.__init__(self, persistFile, {
      "formatId": "3u_eurorack",
      "widthInHp": 6,
      "panelHeight": 0.2,
      "anchorPoint": "top-left",
      "supportType": "none",
      "supportSolidHeight": 0.2,
      "supportShellHeight": 0.9,
      "supportShellWallThickness": 0.1,
    })
    self.formatId: str
    self.widthInHp: int
    self.panelHeight: float
    self.anchorPoint: str
    self.supportType: str
    self.supportSolidHeight: float
    self.supportShellHeight: float
    self.supportShellWallThickness: float

  def restoreDefaults(self):
    super().restoreDefaults()
    self.ensureDefaultKeyIsValid("formatId", self.__formatData)
    self.ensureDefaultKeyIsValid("anchorPoint", self.__anchorPoints)
    self.ensureDefaultKeyIsValid("supportType", self.__supportTypes)

  # anchorPoint getters and setters by name for the Fusion UI
  @property
  def anchorPointNames(self):
    return self.__anchorPoints.values()
  
  @property
  def anchorPointName(self):
    return self.__anchorPoints[self.anchorPoint]
  
  def getIdForAnchorPointName(self, name: str):
    return next(key for key, value in self.__anchorPoints.items() if value == name)

  @anchorPointName.setter
  def anchorPointName(self, name: str):
    self.anchorPoint = self.getIdForAnchorPointName(name)

  # supportType getters and setters by name for the Fusion UI
  @property
  def supportTypeNames(self):
    return self.__supportTypes.values()
  
  @property
  def supportTypeName(self):
    return self.__supportTypes[self.supportType]
  
  def getIdForSupportTypeName(self, name: str):
    return next(key for key, value in self.__supportTypes.items() if value == name)

  @supportTypeName.setter
  def supportTypeName(self, name: str):
    self.supportType = self.getIdForSupportTypeName(name)

  # formatId getters and setters by name for the Fusion UI
  @property
  def formatNames(self):
    return [obj["name"] for obj in self.__formatData.values() if "name" in obj]
  
  @property
  def formatName(self):
    return self.__formatData[self.formatId]["name"]
  
  def getIdForFormatName(self, name: str):
    return next(key for key, value in self.__formatData.items() if "name" in value and value["name"] == name)

  @formatName.setter
  def formatName(self, name: str):
    self.formatId = self.getIdForFormatName(name)

  # Format data getters
  def __formatValue(self, key: str):
    return (self.__formatData["__defaults"] | self.__formatData[self.formatId])[key]
  
  @property
  def width(self):
    return self.__formatValue("hpWidth") * self.widthInHp
  
  @property
  def widthAsExpression(self):
    # Ensure value is specified as HP * hpWidth in the user's default units for easy adjustments later
    design = adsk.fusion.Design.cast(app.activeProduct)
    unitsMgr = design.fusionUnitsManager
    return '{} * {}'.format(self.widthInHp, unitsMgr.formatValue(self.__formatValue("hpWidth")))

  @property
  def panelLength(self):
    return self.__formatValue("panelLength")

  @property
  def maxPcbLength(self):
    return self.__formatValue("maxPcbLength")

  @property
  def slotDiameter(self):
    return self.__formatValue("slotDiameter")

  @property
  def slotLength(self):
    return self.__formatValue("slotLength")

  @property
  def slotOffsetY(self):
    return self.__formatValue("slotOffsetY")

  @property
  def slotOffsetX(self):
    return self.__formatValue("slotOffsetX")

