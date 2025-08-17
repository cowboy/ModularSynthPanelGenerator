import adsk.core, adsk.fusion
from ..generalUtils.persist_utils import Persistable

app = adsk.core.Application.get()

# All numeric values are in cm, which is the default for the Fusion API

class EurorackPanelOptions(Persistable):
  # These values shouldn't need to change
  slotDiameter: float = 0.35
  slotLength: float = 0.15
  slotOffsetY: float = 0.3

  # These values probably shouldn't be accessed directly
  __slotOffsetX: float = 0.687
  __hpWidth: float = 0.508
  __anchorPoints = {
      "top-left": "Top Left",
      "top-right": "Top Right",
      "bottom-left": "Bottom Left",
      "bottom-right": "Bottom Right",
  }
  __supportTypes = {
    "none": "No reinforcements",
    "solid": "Solid (for blanks)",
    "shell": "Shell (for point-to-point switches/jacks)",
  }
  __formatTypes = {
    "3u": {
      "name": "3U",
      "length": 12.85,
      "railLength": 0.925,
    },
    "1u_intellijel": {
      "name": "1U (Intellijel)",
      "length": 3.965,
      "railLength": 0.8325,
    },
  }
  
  def __init__(self, persistFile: str):
    Persistable.__init__(self, persistFile, {
      "formatId": "3u",
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
    return [obj["name"] for obj in self.__formatTypes.values()]
  
  @property
  def formatName(self):
    return self.__formatTypes[self.formatId]["name"]
  
  def getIdForFormatName(self, name: str):
    return next(key for key, value in self.__formatTypes.items() if value["name"] == name)

  @formatName.setter
  def formatName(self, name: str):
    self.formatId = self.getIdForFormatName(name)

  # Misc getters
  @property
  def width(self):
    return self.__hpWidth * self.widthInHp
  
  @property
  def widthAsExpression(self):
    design = adsk.fusion.Design.cast(app.activeProduct)
    unitsMgr = design.fusionUnitsManager
    return '{} * {}'.format(self.widthInHp, unitsMgr.formatValue(self.__hpWidth))

  @property
  def length(self):
    return self.__formatTypes[self.formatId]["length"]

  @property
  def railLength(self):
    return self.__formatTypes[self.formatId]["railLength"]
  
  @property
  def slotOffsetX(self):
    if (self.widthInHp == 2):
      return (self.width - self.slotLength) / 2
    else:
      return self.__slotOffsetX
