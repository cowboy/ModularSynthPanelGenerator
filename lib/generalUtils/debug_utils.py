import adsk.core
import adsk.fusion
from ..fusionAddInUtils import log

app = adsk.core.Application.get()
ui = app.userInterface


def alert(msg):
    ui.messageBox(str(msg))


def identifyFaces(body: adsk.fusion.BRepBody):
    component = body.parentComponent
    sketches = component.sketches
    for i, face in enumerate(body.faces):
        try:
            sketch = sketches.add(face)
            sketch.name = "Face {}".format(i)
        except Exception as err:
            log(f"Error occurred, {err}")
