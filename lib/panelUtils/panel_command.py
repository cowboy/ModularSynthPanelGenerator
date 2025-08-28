import adsk.core
import adsk.fusion
import traceback

from .. import fusionAddInUtils as futil
from .panel_inputs import Inputs
from .panel_options import PanelOptions
from .panel_generate import generatePanelComponent

app = adsk.core.Application.get()
ui = app.userInterface

# CommandInputs Object
# https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
#
# Command Inputs
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-8B9041D5-75CC-4515-B4BB-4CF2CD5BC359
#
# Creating Custom Fusion Commands
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-3922697A-7BF1-4799-9A5B-C8539DF57051
#
# Command Inputs API Sample
# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-e5c4dbe8-ee48-11e4-9823-f8b156d7cd97

CMD_NAME = "Modular Synth Panel Generator"
CMD_Description = "Create a modular synth panel"

OPTIONS = PanelOptions("modular_synth_panel_generator.json")
INPUTS: Inputs

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
LOCAL_HANDLERS = []


def log(msg):
    futil.log(f"[{CMD_NAME}] {str(msg)}")


def getErrorMessage(
    text="An unknown error occurred, please validate your inputs and try again",
):
    stackTrace = traceback.format_exc()
    return f"{text}:<br>{stackTrace}"


# Named for easy importing into commandDialog/entry.py
def command_created(args: adsk.core.CommandCreatedEventArgs):
    log("Command Created Event")
    global OPTIONS, INPUTS
    OPTIONS.restoreDefaults()
    INPUTS = Inputs(args.command.commandInputs, OPTIONS)

    args.command.setDialogMinimumSize(400, 450)
    args.command.setDialogSize(400, 450)

    # Register event handlers
    futil.add_handler(args.command.execute, onCommandExecute, local_handlers=LOCAL_HANDLERS)
    futil.add_handler(args.command.executePreview, onCommandPreview, local_handlers=LOCAL_HANDLERS)
    futil.add_handler(args.command.inputChanged, onCommandInputChanged, local_handlers=LOCAL_HANDLERS)
    futil.add_handler(args.command.validateInputs, onCommandValidateInput, local_handlers=LOCAL_HANDLERS)
    futil.add_handler(args.command.destroy, onCommandDestroy, local_handlers=LOCAL_HANDLERS)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def onCommandExecute(args: adsk.core.CommandEventArgs):
    log("Command Execute Event")
    generatePanel(args)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def onCommandPreview(args: adsk.core.CommandEventArgs):
    log("Command Preview Event")
    if INPUTS.isValid:
        generatePanel(args)
    else:
        args.executeFailed = True
        args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def onCommandInputChanged(args: adsk.core.InputChangedEventArgs):
    changedInputId = args.input.id
    log(f"Command Input Changed: {changedInputId}")
    INPUTS.handleAction(changedInputId)


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def onCommandValidateInput(args: adsk.core.ValidateInputsEventArgs):
    log("Validate Input Event")
    global INPUTS

    args.areInputsValid = INPUTS.isValid

    if INPUTS.isValid:
        INPUTS.updateOptionsFromInputs()


# This event handler is called when the command terminates.
def onCommandDestroy(args: adsk.core.CommandEventArgs):
    log("Command Destroy Event")
    global LOCAL_HANDLERS
    LOCAL_HANDLERS = []


def generatePanel(args: adsk.core.CommandEventArgs):
    global OPTIONS
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        if des.designType == 0:
            args.executeFailed = True
            args.executeFailedMessage = "Projects with direct modeling are not supported, please enable parametric modeling (timeline) to proceed."
            return False

        root = adsk.fusion.Component.cast(des.rootComponent)
        componentName = "{} {} HP Panel".format(OPTIONS.formatName, OPTIONS.widthInHp)

        # create new component
        newCmpOcc = adsk.fusion.Occurrences.cast(root.occurrences).addNewComponent(adsk.core.Matrix3D.create())
        newCmpOcc.component.name = componentName
        newCmpOcc.activate()

        panelComponent: adsk.fusion.Component = newCmpOcc.component

        generatePanelComponent(panelComponent, OPTIONS)

        # group features in timeline
        count = panelComponent.sketches.count + panelComponent.features.count + panelComponent.constructionAxes.count + panelComponent.constructionPlanes.count
        if count > 1:
            panelGroup = des.timeline.timelineGroups.add(newCmpOcc.timelineObject.index, newCmpOcc.timelineObject.index + count)
            panelGroup.name = componentName
    except Exception as err:
        args.executeFailed = True
        args.executeFailedMessage = getErrorMessage()
        log(f"Error occurred, {err}, {getErrorMessage()}")
        return False
