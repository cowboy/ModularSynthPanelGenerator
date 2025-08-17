import adsk.core, adsk.fusion, traceback

from .. import fusionAddInUtils as futil
from .eurorack_panel_options import EurorackPanelOptions
from .eurorack_panel import createEurorackPanel

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

CMD_NAME = 'Eurorack Panel Generator'
CMD_Description = 'Create a Eurorack panel'

OPTIONS = EurorackPanelOptions('eurorack_panel.json')
INPUTS: adsk.core.CommandInputs
INPUTS_VALID = True

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
LOCAL_HANDLERS = []

def log(msg):
  futil.log(f'[{CMD_NAME}] {str(msg)}')

def getErrorMessage(text = "An unknown error occurred, please validate your inputs and try again"):
    stackTrace = traceback.format_exc()
    return f"{text}:<br>{stackTrace}"

# Named for easy importing into commandDialog/entry.py
def command_created(args: adsk.core.CommandCreatedEventArgs):
  log('Command Created Event')
  global OPTIONS, INPUTS
  OPTIONS.restoreDefaults()
  INPUTS = args.command.commandInputs

  args.command.setDialogInitialSize(400, 500)

  initializeInputs()
  enableDisableInputs()

  # Register event handlers
  futil.add_handler(args.command.execute, onCommandExecute, local_handlers=LOCAL_HANDLERS)
  futil.add_handler(args.command.executePreview, onCommandPreview, local_handlers=LOCAL_HANDLERS)
  futil.add_handler(args.command.inputChanged, onCommandInputChanged, local_handlers=LOCAL_HANDLERS)
  futil.add_handler(args.command.validateInputs, onCommandValidateInput, local_handlers=LOCAL_HANDLERS)
  futil.add_handler(args.command.destroy, onCommandDestroy, local_handlers=LOCAL_HANDLERS)

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def onCommandExecute(args: adsk.core.CommandEventArgs):
  log('Command Execute Event')
  generateEurorackPanel(args)

# This event handler is called when the command needs to compute a new preview in the graphics window.
def onCommandPreview(args: adsk.core.CommandEventArgs):
  log('Command Preview Event')
  if INPUTS_VALID:
    generateEurorackPanel(args)
  else:
    args.executeFailed = True
    args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def onCommandInputChanged(args: adsk.core.InputChangedEventArgs):
  global OPTIONS
  changedInputId = args.input.id
  log(f'Command Input Changed: {changedInputId}')
  enableDisableInputs()

  if changedInputId == 'restoreDefaults':
    OPTIONS.restoreDefaults()
    updateInputsFromOptions()
  elif changedInputId == 'saveDefaults':
    OPTIONS.saveDefaults()
  elif changedInputId == 'eraseDefaults':
    OPTIONS.eraseDefaults()

# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def onCommandValidateInput(args: adsk.core.ValidateInputsEventArgs):
  log('Validate Input Event')
  global INPUTS, INPUTS_VALID
  
  # Verify the validity of the input values. This controls if the OK button is enabled or not.
  widthInHp: adsk.core.IntegerSpinnerCommandInput = INPUTS.itemById('widthInHp') # type: ignore

  INPUTS_VALID = widthInHp.value >= 2

  args.areInputsValid = INPUTS_VALID

  if INPUTS_VALID:
    updateOptionsFromInputs()

# This event handler is called when the command terminates.
def onCommandDestroy(args: adsk.core.CommandEventArgs):
  log('Command Destroy Event')
  global LOCAL_HANDLERS
  LOCAL_HANDLERS = []

def initializeInputs():
  global INPUTS
  defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

  message = 'For more information, <a href="https://github.com/">click here.</a>'
  INPUTS.addTextBoxCommandInput('textBox', 'Information', message, 1, True)            

  heightDropdown = INPUTS.addDropDownCommandInput('formatType', 'Panel format', adsk.core.DropDownStyles.TextListDropDownStyle) # type: ignore
  for name in OPTIONS.formatNames:
      heightDropdown.listItems.add(name, name == OPTIONS.formatName)

  INPUTS.addIntegerSpinnerCommandInput('widthInHp', 'Panel width in HP', 2, 9000, 1, OPTIONS.widthInHp)
  INPUTS.addValueInput('panelHeight', 'Panel thickness', defaultLengthUnits, adsk.core.ValueInput.createByReal(OPTIONS.panelHeight))

  supportGroup = INPUTS.addGroupCommandInput('supportGroup', 'Reinforcement')
  supportGroup.isExpanded = True

  supportDropdown = supportGroup.children.addDropDownCommandInput('supportType', 'Type', adsk.core.DropDownStyles.TextListDropDownStyle) # type: ignore
  for name in OPTIONS.supportTypeNames:
      supportDropdown.listItems.add(name, name == OPTIONS.supportTypeName)
  
  supportGroup.children.addValueInput('supportSolidHeight', 'Support thickness', defaultLengthUnits, adsk.core.ValueInput.createByReal(OPTIONS.supportSolidHeight))
  supportGroup.children.addValueInput('supportShellHeight', 'Shell thickness', defaultLengthUnits, adsk.core.ValueInput.createByReal(OPTIONS.supportShellHeight))
  supportGroup.children.addValueInput('supportShellWallThickness', 'Shell wall thickness', defaultLengthUnits, adsk.core.ValueInput.createByReal(OPTIONS.supportShellWallThickness))

  # Save, restore and erase defaults
  restoreDefaultsInput = INPUTS.addBoolValueInput('restoreDefaults', 'Reset', False, '', False)
  restoreDefaultsInput.text = 'Reset all panel settings to defaults'

  persistGroup = INPUTS.addGroupCommandInput('persistGroup', 'Save defaults')
  persistGroup.isExpanded = False
  saveDefaultsInput = persistGroup.children.addBoolValueInput('saveDefaults', 'Update defaults', False, '', False)
  saveDefaultsInput.text = 'Save current panel settings as new defaults'
  eraseDefaultsInput = persistGroup.children.addBoolValueInput('eraseDefaults', 'Factory reset', False, '', False)
  eraseDefaultsInput.text = 'Erase saved panel settings defaults'

def enableDisableInputs():
  global INPUTS

  supportTypeInput = INPUTS.itemById('supportType')
  if supportTypeInput:
    defaults = EurorackPanelOptions('panel_options.json')
    supportTypeId = defaults.getIdForSupportTypeName(supportTypeInput.selectedItem.name) # type: ignore

    INPUTS.itemById('supportSolidHeight').isVisible = supportTypeId == 'solid'
    INPUTS.itemById('supportShellHeight').isVisible = supportTypeId == 'shell'
    INPUTS.itemById('supportShellWallThickness').isVisible = supportTypeId == 'shell'

def updateOptionsFromInputs():
    global OPTIONS, INPUTS

    formatType: adsk.core.DropDownCommandInput = INPUTS.itemById('formatType') # type: ignore
    OPTIONS.formatName = formatType.selectedItem.name

    widthInHp: adsk.core.IntegerSpinnerCommandInput = INPUTS.itemById('widthInHp') # type: ignore
    OPTIONS.widthInHp = int(widthInHp.value)

    panelHeight: adsk.core.addValueInput = INPUTS.itemById('panelHeight') # type: ignore
    OPTIONS.panelHeight = panelHeight.value

    supportType: adsk.core.DropDownCommandInput = INPUTS.itemById('supportType') # type: ignore
    OPTIONS.supportTypeName = supportType.selectedItem.name

    supportSolidHeight: adsk.core.addValueInput = INPUTS.itemById('supportSolidHeight') # type: ignore
    OPTIONS.supportSolidHeight = supportSolidHeight.value

    supportShellHeight: adsk.core.addValueInput = INPUTS.itemById('supportShellHeight') # type: ignore
    OPTIONS.supportShellHeight = supportShellHeight.value

    supportShellWallThickness: adsk.core.addValueInput = INPUTS.itemById('supportShellWallThickness') # type: ignore
    OPTIONS.supportShellWallThickness = supportShellWallThickness.value

def updateInputsFromOptions():
    global OPTIONS, INPUTS

    formatType: adsk.core.DropDownCommandInput = INPUTS.itemById('formatType') # type: ignore
    for listItem in formatType.listItems:
        listItem.isSelected = listItem.name == OPTIONS.formatName

    widthInHp: adsk.core.IntegerSpinnerCommandInput = INPUTS.itemById('widthInHp') # type: ignore
    widthInHp.value = OPTIONS.widthInHp

    panelHeight: adsk.core.addValueInput = INPUTS.itemById('panelHeight') # type: ignore
    panelHeight.value = OPTIONS.panelHeight

    supportType: adsk.core.DropDownCommandInput = INPUTS.itemById('supportType') # type: ignore
    for listItem in supportType.listItems:
        listItem.isSelected = listItem.name == OPTIONS.supportTypeName

    supportSolidHeight: adsk.core.addValueInput = INPUTS.itemById('supportSolidHeight') # type: ignore
    supportSolidHeight.value = OPTIONS.supportSolidHeight

    supportShellHeight: adsk.core.addValueInput = INPUTS.itemById('supportShellHeight') # type: ignore
    supportShellHeight.value = OPTIONS.supportShellHeight

    supportShellWallThickness: adsk.core.addValueInput = INPUTS.itemById('supportShellWallThickness') # type: ignore
    supportShellWallThickness.value = OPTIONS.supportShellWallThickness

def generateEurorackPanel(args: adsk.core.CommandEventArgs):
  global OPTIONS
  try:
    des = adsk.fusion.Design.cast(app.activeProduct)
    if des.designType == 0:
      args.executeFailed = True
      args.executeFailedMessage = 'Projects with direct modeling are not supported, please enable parametric modeling (timeline) to proceed.'
      return False
    
    root = adsk.fusion.Component.cast(des.rootComponent)
    componentName = '{} {} HP Panel'.format(OPTIONS.formatName, OPTIONS.widthInHp)

    # create new component
    newCmpOcc = adsk.fusion.Occurrences.cast(root.occurrences).addNewComponent(adsk.core.Matrix3D.create())
    newCmpOcc.component.name = componentName
    newCmpOcc.activate()

    eurorackPanelComponent: adsk.fusion.Component = newCmpOcc.component

    createEurorackPanel(OPTIONS, eurorackPanelComponent)

    # group features in timeline
    count = eurorackPanelComponent.sketches.count + eurorackPanelComponent.features.count + eurorackPanelComponent.constructionAxes.count + eurorackPanelComponent.constructionPlanes.count
    eurorackPanelGroup = des.timeline.timelineGroups.add(newCmpOcc.timelineObject.index, newCmpOcc.timelineObject.index + count)
    eurorackPanelGroup.name = componentName
  except Exception as err:
    args.executeFailed = True
    args.executeFailedMessage = getErrorMessage()
    log(f'Error occurred, {err}, {getErrorMessage()}')
    return False
