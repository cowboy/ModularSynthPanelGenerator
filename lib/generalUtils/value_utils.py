import adsk.core
import adsk.fusion

# ValueInput Object
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-bdeb52e0-a6af-4909-93e8-3b13acd0e39c

app = adsk.core.Application.get()


def getNormalizedValueInput(length: float):
    design = adsk.fusion.Design.cast(app.activeProduct)
    unitsMgr = design.fusionUnitsManager
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    converted = round(unitsMgr.convert(length, "cm", defaultLengthUnits), 3)
    return adsk.core.ValueInput.createByString(f"{converted} {defaultLengthUnits}")
