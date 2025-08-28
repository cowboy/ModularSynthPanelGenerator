import adsk.core
import adsk.fusion
from .value_utils import getNormalizedValueInput
from typing import TypedDict, NotRequired, Unpack

# Extrude Feature API Sample
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-CB1A2357-C8CD-474D-921E-992CA3621D04

app = adsk.core.Application.get()


class ExtrudeKwargs(TypedDict):
    operation: NotRequired[adsk.fusion.FeatureOperations]
    offsetFrom: NotRequired[adsk.core.Base]


def extrude(
    component: adsk.fusion.Component,
    sketch: adsk.fusion.Sketch,
    profileIndices: list[int],
    height: float,
    name: str,
    **kwargs: Unpack[ExtrudeKwargs],
):
    operation = kwargs.get("operation", adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    offsetFrom = kwargs.get("offsetFrom")

    profiles = adsk.core.ObjectCollection.create()
    for i in profileIndices:
        profiles.add(sketch.profiles.item(i))

    features = component.features
    extrudeFeatures = features.extrudeFeatures

    extrudeInput = extrudeFeatures.createInput(profiles, operation)  # type: ignore
    extent = adsk.fusion.DistanceExtentDefinition.create(getNormalizedValueInput(height))
    extrudeInput.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)  # type: ignore
    if offsetFrom:
        extrudeInput.startExtent = adsk.fusion.FromEntityStartDefinition.create(offsetFrom, adsk.core.ValueInput.createByReal(0))

    extrude = extrudeFeatures.add(extrudeInput)
    extrude.name = "Extrude {}".format(name)
    body = extrude.bodies.item(0)
    return body
