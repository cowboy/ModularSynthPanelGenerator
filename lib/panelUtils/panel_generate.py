import adsk.core, adsk.fusion
from ..generalUtils.sketch_utils import addPoints, constrainPointToPoint, constrainRectangleWidthHeight, lineMidpoint, midpoint, point, sketchLineMidpoint, sketchRectangle, sketchSlot
from ..generalUtils.extrude_utils import extrude
from .panel_options import PanelOptions
from .. import fusionAddInUtils as futil

app = adsk.core.Application.get()
ui = app.userInterface

def generatePanelComponent(component: adsk.fusion.Component, opts: PanelOptions):
  sketches = component.sketches
  xyPlane = component.xYConstructionPlane
  sketch = sketches.add(xyPlane)
  lines = sketch.sketchCurves.sketchLines
  constraints = sketch.geometricConstraints
  dimensions = sketch.sketchDimensions

  sketch.name = "Panel"
  sketch.areDimensionsShown = True

  # Panel
  anchorPointVertical, anchorPointHorizontal = opts.anchorPoint.split('-')
  match anchorPointVertical:
    case 'top':
      panelStartY = -opts.panelLength
    case 'middle':
      panelStartY = -opts.panelLength / 2
    case 'bottom':
      panelStartY = 0
    case _:
      raise ValueError('Invalid anchorPoint value')

  match anchorPointHorizontal:
    case 'left':
      panelStartX = 0
    case 'center':
      panelStartX = -opts.width / 2
    case 'right':
      panelStartX = -opts.width
    case _:
      raise ValueError('Invalid anchorPoint value')

  panelStartPoint = point(panelStartX, panelStartY)

  rectangleLines = sketchRectangle(sketch, panelStartPoint, opts.width, opts.panelLength)
  constrainRectangleWidthHeight(sketch, rectangleLines)
  dimensions.item(dimensions.count - 2).parameter.expression = opts.widthAsExpression
  
  panelBottomLine = rectangleLines.item(0)
  panelRightLine = rectangleLines.item(1)
  panelTopLine = rectangleLines.item(2)
  panelLeftLine = rectangleLines.item(3)

  topLeftPoint = panelTopLine.endSketchPoint
  topRightPoint = panelTopLine.startSketchPoint
  bottomLeftPoint = panelBottomLine.startSketchPoint
  bottomRightPoint = panelBottomLine.endSketchPoint

  def createPanelHorizontalLine(offset: float, isConstruction: bool):
    line = lines.addByTwoPoints(
      point(panelTopLine.startSketchPoint.geometry.x, offset),
      point(panelTopLine.endSketchPoint.geometry.x, offset)
    )
    line.isConstruction = isConstruction
    constraints.addHorizontal(line)
    constraints.addCoincident(line.startSketchPoint, panelLeftLine)
    constraints.addCoincident(line.endSketchPoint, panelRightLine)
    return line

  def createPanelMidLine():
    line = createPanelHorizontalLine(lineMidpoint(panelLeftLine).y, True)
    constraints.addMidPoint(line.startSketchPoint, panelLeftLine)
    return line
  
  match opts.anchorPoint:
    case 'top-left':
      anchorPoint = topLeftPoint
    case 'top-center':
      anchorPoint = sketchLineMidpoint(sketch, panelTopLine)
    case 'top-right':
      anchorPoint = topRightPoint
    case 'middle-left':
      anchorPoint = sketchLineMidpoint(sketch, panelLeftLine)
    case 'middle-center':
      anchorPoint = sketchLineMidpoint(sketch, createPanelMidLine())
    case 'middle-right':
      anchorPoint = sketchLineMidpoint(sketch, panelRightLine)
    case 'bottom-left':
      anchorPoint = bottomLeftPoint
    case 'bottom-center':
      anchorPoint = sketchLineMidpoint(sketch, panelBottomLine)
    case 'bottom-right':
      anchorPoint = bottomRightPoint

  constrainPointToPoint(sketch, anchorPoint, sketch.originPoint)

  # Max extents for anything extruded from the bottom
  def addRefLine(panelLine: adsk.fusion.SketchLine, offset: float):
    line = createPanelHorizontalLine(panelLine.startSketchPoint.geometry.y + offset, opts.supportType == 'none')
    dimensions.addDistanceDimension(
      panelLine.startSketchPoint,
      line.startSketchPoint,
      adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, # type: ignore
      midpoint(lineMidpoint(line), lineMidpoint(panelLine))
    )
    return line

  railLength = (opts.panelLength - opts.maxPcbLength) / 2
  topRefLine = addRefLine(panelTopLine, -railLength)
  bottomRefLine = addRefLine(panelBottomLine, railLength)

  dimensions.addDistanceDimension(
    topRefLine.startSketchPoint,
    bottomRefLine.startSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, # type: ignore
    addPoints(midpoint(topRefLine.startSketchPoint.geometry, bottomRefLine.startSketchPoint.geometry), point(-0.2, 0)),
    False
  )

  if opts.supportType == 'shell':
    shellRectLines = sketchRectangle(sketch, bottomRefLine.startSketchPoint.geometry, opts.width, opts.maxPcbLength, offset=opts.supportShellWallThickness)
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
    slots.append([topLeftPoint, -1, 1])
    slots.append([bottomLeftPoint, 1, 1])

  if (slotsRight):
    slots.append([topRightPoint, -1, -1])
    slots.append([bottomRightPoint, 1, -1])

  slotFaceCount = 4 * len(slots)

  for referencePoint, yOffsetDirection, xOffsetDirection in slots:
    slotStartPoint = addPoints(referencePoint.geometry, point(xOffsetDirection * opts.slotOffsetX, yOffsetDirection * opts.slotOffsetY))
    slotEndPoint = addPoints(slotStartPoint, point(xOffsetDirection * opts.slotLength, 0))
    slotCenterLine = sketchSlot(sketch, slotStartPoint, slotEndPoint, opts.slotDiameter)[0]
    constrainPointToPoint(sketch, slotCenterLine.startSketchPoint, referencePoint)

  # return

  # Extrusions
  if opts.supportType == 'solid':
    body1 = extrude(component, sketch, [0, 1, 2], -opts.panelHeight, "Panel")
    body = extrude(component, sketch, [1], -opts.supportSolidHeight, "Support", offsetFrom=body1.faces.item(5 + slotFaceCount), operation=adsk.fusion.FeatureOperations.JoinFeatureOperation) # type: ignore
  elif opts.supportType == 'shell':
    body1 = extrude(component, sketch, [0, 1, 2, 3], -opts.panelHeight, "Panel")
    body = extrude(component, sketch, [1], -opts.supportShellHeight, "Support Shell", offsetFrom=body1.faces.item(5 + slotFaceCount), operation=adsk.fusion.FeatureOperations.JoinFeatureOperation) # type: ignore
  else:
    body = extrude(component, sketch, [0], -opts.panelHeight, "Panel")

  body.name = "Panel"

