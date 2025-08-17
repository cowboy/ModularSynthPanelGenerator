import adsk.core, adsk.fusion
from ..generalUtils.sketch_utils import addPoints, constrainPointToPoint, constrainRectangleWidthHeight, lineMidpoint, midpoint, point, sketchRectangle, sketchSlot
from ..generalUtils.extrude_utils import extrude
from .eurorack_panel_options import EurorackPanelOptions

# https://fusion360-api-cheatsheet.github.io/
#
# GridfinityGenerator (major inspiration for this project)
# https://github.com/Le0Michine/FusionGridfinityGenerator/
# https://apps.autodesk.com/FUSION/en/Detail/Index?id=7197558650811789

app = adsk.core.Application.get()
ui = app.userInterface

def createEurorackPanel(opts: EurorackPanelOptions, component: adsk.fusion.Component):
  sketches = component.sketches
  xyPlane = component.xYConstructionPlane
  sketch = sketches.add(xyPlane)
  lines = sketch.sketchCurves.sketchLines
  constraints = sketch.geometricConstraints
  dimensions = sketch.sketchDimensions

  sketch.name = "Panel"
  sketch.areDimensionsShown = True

  # Panel
  rectangleLines = sketchRectangle(sketch, point(0, 0), opts.width, opts.length)
  constrainRectangleWidthHeight(sketch, rectangleLines)
  dimensions.item(dimensions.count - 2).parameter.expression = opts.widthAsExpression
  panelBottomLine = rectangleLines.item(0)
  panelRightLine = rectangleLines.item(1)
  panelTopLine = rectangleLines.item(2)
  panelLeftLine = rectangleLines.item(3)
  rectOriginSketchPoint = panelBottomLine.startSketchPoint
  constrainPointToPoint(sketch, rectOriginSketchPoint, sketch.originPoint)

  # Max extents for anything extruded from the bottom
  def addRefLine(panelLine: adsk.fusion.SketchLine, offset: float):
    line = lines.addByTwoPoints(
      addPoints(panelLine.startSketchPoint.geometry, point(0, offset)),
      addPoints(panelLine.endSketchPoint.geometry, point(0, offset))
    )
    line.isConstruction = opts.supportType == 'none'
    dimensions.addDistanceDimension(
      panelLine.startSketchPoint,
      line.startSketchPoint,
      adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, # type: ignore
      addPoints(midpoint(line.startSketchPoint.geometry, panelLine.startSketchPoint.geometry), point(-0.2, 0))
    )
    constraints.addHorizontal(line)
    constraints.addCoincident(line.startSketchPoint, panelLeftLine)
    constraints.addCoincident(line.endSketchPoint, panelRightLine)
    return line

  topRefLine = addRefLine(panelTopLine, -opts.railLength)
  bottomRefLine = addRefLine(panelBottomLine, opts.railLength)

  if opts.supportType == 'shell':
    shellRectLines = sketchRectangle(sketch, point(0, opts.railLength), opts.width, opts.length - (2 * opts.railLength), offset=opts.supportShellWallThickness)
    shellBottomLine = shellRectLines.item(0)
    shellRightLine = shellRectLines.item(1)
    shellTopLine = shellRectLines.item(2)
    shellLeftLine = shellRectLines.item(3)
    dimensions.addOffsetDimension(bottomRefLine, shellBottomLine, lineMidpoint(shellBottomLine))
    dimensions.addOffsetDimension(panelRightLine, shellRightLine, lineMidpoint(shellRightLine))
    dimensions.addOffsetDimension(topRefLine, shellTopLine, lineMidpoint(shellTopLine))
    dimensions.addOffsetDimension(panelLeftLine, shellLeftLine, lineMidpoint(shellLeftLine))

  # Screw holes
  slots = []
  slotsLeft = True
  slotsRight = True

  if (opts.widthInHp < 6):
    slotsRight = False

  if (slotsLeft):
    slots.append([rectOriginSketchPoint, 1, 1])
    slots.append([rectangleLines.item(2).endSketchPoint, -1, 1])

  if (slotsRight):
    slots.append([rectangleLines.item(1).endSketchPoint, -1, -1])
    slots.append([rectangleLines.item(0).endSketchPoint, 1, -1])

  slotFaces = 4 * len(slots)

  for referencePoint, yOffsetDirection, xOffsetDirection in slots:
    slotStartPoint = addPoints(referencePoint.geometry, point(xOffsetDirection * opts.slotOffsetX, yOffsetDirection * opts.slotOffsetY))
    slotEndPoint = addPoints(slotStartPoint, point(xOffsetDirection * opts.slotLength, 0))
    slotCenterLine = sketchSlot(sketch, slotStartPoint, slotEndPoint, opts.slotDiameter)[0]
    constrainPointToPoint(sketch, slotCenterLine.startSketchPoint, referencePoint)

  # Extrusions
  if opts.supportType == 'solid':
    body1 = extrude(component, sketch, [0, 1, 2], -opts.panelHeight, "Panel")
    body = extrude(component, sketch, [1], -opts.supportSolidHeight, "Support", offsetFrom=body1.faces.item(5 + slotFaces), operation=adsk.fusion.FeatureOperations.JoinFeatureOperation) # type: ignore
  elif opts.supportType == 'shell':
    body1 = extrude(component, sketch, [0, 1, 2, 3], -opts.panelHeight, "Panel")
    body = extrude(component, sketch, [1], -opts.supportShellHeight, "Support Shell", offsetFrom=body1.faces.item(5 + slotFaces), operation=adsk.fusion.FeatureOperations.JoinFeatureOperation) # type: ignore
  else:
    body = extrude(component, sketch, [0], -opts.panelHeight, "Panel")

  body.name = "Panel"

