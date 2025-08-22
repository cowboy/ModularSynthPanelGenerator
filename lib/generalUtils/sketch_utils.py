import adsk.core, adsk.fusion
import math
from typing import TypedDict, NotRequired, Unpack

# Sketch Object
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-2367ed6a-0ad1-4c8f-935e-b52738d1ce2b
#
# Sketch Sample API Sample
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-da476794-86f9-11e7-937e-6c0b84aa5a3f

def point(x: float, y: float):
  return adsk.core.Point3D.create(x, y, 0)

def addPoints(a: adsk.core.Point3D, b: adsk.core.Point3D):
  return point(a.x + b.x, a.y + b.y)

def multPoints(a: adsk.core.Point3D, b: adsk.core.Point3D):
  return point(a.x * b.x, a.y * b.y)

def midpoint(a: adsk.core.Point3D, b: adsk.core.Point3D):
  return point((a.x + b.x) / 2, (a.y + b.y) / 2)

def lineMidpoint(line: adsk.fusion.SketchLine, offset: float = 0):
  m = midpoint(line.startSketchPoint.geometry, line.endSketchPoint.geometry)
  if (offset):
    m = addPoints(m, lineOffset(line, offset))
  return m

def lineOffset(line: adsk.fusion.SketchLine, offset: float):
  ratio = offset / line.length
  deltaX = (line.endSketchPoint.geometry.y - line.startSketchPoint.geometry.y) * ratio
  deltaY = (line.endSketchPoint.geometry.x - line.startSketchPoint.geometry.x) * ratio
  return point(deltaX, deltaY)

def sketchLineMidpoint(sketch: adsk.fusion.Sketch, refLine: adsk.fusion.SketchLine):
  points = sketch.sketchPoints
  constraints = sketch.geometricConstraints

  anchorPoint = points.add(lineMidpoint(refLine))
  constraints.addMidPoint(anchorPoint, refLine)
  
  return anchorPoint

class SketchRectangleKwargs(TypedDict):
  offset: NotRequired[float]

def sketchRectangle(
  sketch: adsk.fusion.Sketch,
  startPoint: adsk.core.Point3D,
  width: float,
  length: float,
  **kwargs: Unpack[SketchRectangleKwargs]
):
  lines = sketch.sketchCurves.sketchLines
  constraints = sketch.geometricConstraints

  offset = kwargs.get('offset', 0)
  rectangleLines = lines.addTwoPointRectangle(addPoints(startPoint, point(offset, offset)), addPoints(startPoint, point(width - offset, length - offset)))
  
  constraints.addHorizontal(rectangleLines.item(0))
  constraints.addVertical(rectangleLines.item(1))
  constraints.addHorizontal(rectangleLines.item(2))
  constraints.addVertical(rectangleLines.item(3))

  return rectangleLines

def sketchSlot(
  sketch: adsk.fusion.Sketch,
  startPoint: adsk.core.Point3D,
  endPoint: adsk.core.Point3D,
  diameter: float,  
):
  lines = sketch.sketchCurves.sketchLines
  constraints = sketch.geometricConstraints
  dimensions = sketch.sketchDimensions

  # Sadly, this doesn't seem to return anything of use
  # result = sketch.addCenterToCenterSlot(startPoint, endPoint, adsk.core.ValueInput.createByReal(diameter), True)

  centerLine = lines.addByTwoPoints(startPoint, endPoint)
  centerLine.isConstruction = True
  delta = lineOffset(centerLine, diameter / 2)

  line1Delta = multPoints(delta, point(-1, 1))
  line1Start = addPoints(startPoint, line1Delta)
  line1End = addPoints(endPoint, line1Delta)
  line1 = lines.addByTwoPoints(line1Start, line1End)

  line2Delta = multPoints(delta, point(1, -1))
  line2Start = addPoints(startPoint, line2Delta)
  line2End = addPoints(endPoint, line2Delta)
  line2 = lines.addByTwoPoints(line2Start, line2End)

  arcs = sketch.sketchCurves.sketchArcs
  arc1 = arcs.addByCenterStartSweep(centerLine.startSketchPoint, line1.startSketchPoint, math.pi)
  arc2 = arcs.addByCenterStartSweep(centerLine.endSketchPoint, line2.endSketchPoint, math.pi)

  constraints.addParallel(line1, line2)

  constraints.addCoincident(arc1.centerSketchPoint, centerLine.startSketchPoint)
  constraints.addCoincident(arc2.centerSketchPoint, centerLine.endSketchPoint)
  constraints.addCoincident(arc1.endSketchPoint, line2.startSketchPoint)
  constraints.addCoincident(arc2.endSketchPoint, line1.endSketchPoint)

  constraints.addTangent(line1, arc1)
  constraints.addTangent(line1, arc2)
  constraints.addTangent(line2, arc1)
  constraints.addTangent(line2, arc2)
  
  dimensions.addDiameterDimension(arc1, midpoint(arc1.endSketchPoint.geometry, centerLine.startSketchPoint.geometry))
  
  constrainPointToPoint(sketch, centerLine.startSketchPoint, centerLine.endSketchPoint)

  return centerLine, lines, arcs

def constrainRectangleWidthHeight(
  sketch: adsk.fusion.Sketch,
  lines: adsk.fusion.SketchLineList,
  labelOffset: float = 0.2
):
  dimensions = sketch.sketchDimensions
  dimensions.addDistanceDimension(lines.item(0).startSketchPoint,
    lines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, # type: ignore
    lineMidpoint(lines.item(0), -labelOffset))
  dimensions.addDistanceDimension(lines.item(1).startSketchPoint,
    lines.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, # type: ignore
    lineMidpoint(lines.item(1), labelOffset))

def constrainPointToPoint(
  sketch: adsk.fusion.Sketch,
  sketchPoint: adsk.fusion.SketchPoint,
  referencePoint: adsk.fusion.SketchPoint
):
  constraints = sketch.geometricConstraints
  dimensions = sketch.sketchDimensions

  if sketchPoint.geometry.isEqualTo(referencePoint.geometry):
    constraints.addCoincident(referencePoint, sketchPoint)
  else:
    dimensions.addDistanceDimension(
      referencePoint,
      sketchPoint,
      adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, # type: ignore
      midpoint(point(referencePoint.geometry.x, sketchPoint.geometry.y), sketchPoint.geometry)
    )
    dimensions.addDistanceDimension(
      referencePoint,
      sketchPoint,
      adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, # type: ignore
      midpoint(point(sketchPoint.geometry.x, referencePoint.geometry.y), sketchPoint.geometry)
    )

