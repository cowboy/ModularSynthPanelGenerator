import adsk.core
from enum import Enum
from typing import cast

app = adsk.core.Application.get()
ui = app.userInterface


class Actions(Enum):
    RESTORE_DEFAULTS = "RESTORE_DEFAULTS"
    SAVE_DEFAULTS = "SAVE_DEFAULTS"
    ERASE_DEFAULTS = "ERASE_DEFAULTS"


class Inputs:
    def __init__(self, inputs: adsk.core.CommandInputs, options):
        self.inputs = inputs
        self.options = options

        self.initializeInputs()

        self.widthInHp = adsk.core.IntegerSpinnerCommandInput.cast(self.inputs.itemById("widthInHp"))
        self.panelHeight = adsk.core.ValueCommandInput.cast(self.inputs.itemById("panelHeight"))
        self.supportSolidHeight = adsk.core.ValueCommandInput.cast(self.inputs.itemById("supportSolidHeight"))
        self.supportShellHeight = adsk.core.ValueCommandInput.cast(self.inputs.itemById("supportShellHeight"))
        self.supportShellWallThickness = adsk.core.ValueCommandInput.cast(self.inputs.itemById("supportShellWallThickness"))
        self.formatType = adsk.core.DropDownCommandInput.cast(self.inputs.itemById("formatType"))
        self.anchorPoint = adsk.core.DropDownCommandInput.cast(self.inputs.itemById("anchorPoint"))
        self.supportType = adsk.core.DropDownCommandInput.cast(self.inputs.itemById("supportType"))

        self.updateUiState()

    def updateUiState(self):
        supportTypeName = self.supportType.selectedItem.name
        supportTypeId = self.options.getIdForSupportTypeName(supportTypeName)
        self.supportSolidHeight.isVisible = supportTypeId == "solid"
        self.supportShellHeight.isVisible = supportTypeId == "shell"
        self.supportShellWallThickness.isVisible = supportTypeId == "shell"

    def updateOptionsFromInputs(self):
        self.options.widthInHp = int(self.widthInHp.value)
        self.options.panelHeight = self.panelHeight.value
        self.options.supportSolidHeight = self.supportSolidHeight.value
        self.options.supportShellHeight = self.supportShellHeight.value
        self.options.supportShellWallThickness = self.supportShellWallThickness.value
        self.options.formatName = self.formatType.selectedItem.name
        self.options.anchorPointName = self.anchorPoint.selectedItem.name
        self.options.supportTypeName = self.supportType.selectedItem.name

    def updateInputsFromOptions(self):
        self.widthInHp.value = self.options.widthInHp
        self.panelHeight.value = self.options.panelHeight
        self.supportSolidHeight.value = self.options.supportSolidHeight
        self.supportShellHeight.value = self.options.supportShellHeight
        self.supportShellWallThickness.value = self.options.supportShellWallThickness
        for listItem in self.formatType.listItems:
            listItem.isSelected = listItem.name == self.options.formatName
        for listItem in self.anchorPoint.listItems:
            listItem.isSelected = listItem.name == self.options.anchorPointName
        for listItem in self.supportType.listItems:
            listItem.isSelected = listItem.name == self.options.supportTypeName

    @property
    def isValid(self):
        return self.widthInHp.value >= 2

    def handleAction(self, action: str):
        self.updateUiState()

        match action:
            case Actions.RESTORE_DEFAULTS.value:
                self.options.restoreDefaults()
                self.updateInputsFromOptions()
            case Actions.SAVE_DEFAULTS.value:
                if not self.options.saveDefaults():
                    ui.messageBox(f"Unable to save defaults file {self.options.persistFile}. Is it writable?", "Warning")
            case Actions.ERASE_DEFAULTS.value:
                if not self.options.eraseDefaults():
                    ui.messageBox(f"Unable to erase defaults file {self.options.persistFile}. Is it writable?", "Warning")

    def initializeInputs(self):
        defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

        message = 'For more information, <a href="https://github.com/cowboy/ModularSynthPanelGenerator">read the documentation.</a>'
        self.inputs.addTextBoxCommandInput("infoTextBox", "Information", message, 1, True)

        heightDropdown = self.inputs.addDropDownCommandInput(
            "formatType", "Panel format", cast(adsk.core.DropDownStyles, adsk.core.DropDownStyles.TextListDropDownStyle)
        )
        for name in self.options.formatNames:
            heightDropdown.listItems.add(name, name == self.options.formatName)

        self.inputs.addIntegerSpinnerCommandInput("widthInHp", "Panel width in HP", 2, 9000, 1, self.options.widthInHp)
        self.inputs.addValueInput(
            "panelHeight",
            "Panel thickness",
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(self.options.panelHeight),
        )

        anchorPointDropdown = self.inputs.addDropDownCommandInput(
            "anchorPoint", "Anchor point", cast(adsk.core.DropDownStyles, adsk.core.DropDownStyles.TextListDropDownStyle)
        )
        for name in self.options.anchorPointNames:
            anchorPointDropdown.listItems.add(name, name == self.options.anchorPointName)

        supportGroup = self.inputs.addGroupCommandInput("supportGroup", "Reinforcement")
        supportGroup.isExpanded = True

        supportTypeDropdown = supportGroup.children.addDropDownCommandInput(
            "supportType", "Type", cast(adsk.core.DropDownStyles, adsk.core.DropDownStyles.TextListDropDownStyle)
        )
        for name in self.options.supportTypeNames:
            supportTypeDropdown.listItems.add(name, name == self.options.supportTypeName)

        supportGroup.children.addValueInput(
            "supportSolidHeight",
            "Support thickness",
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(self.options.supportSolidHeight),
        )
        supportGroup.children.addValueInput(
            "supportShellHeight",
            "Shell thickness",
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(self.options.supportShellHeight),
        )
        supportGroup.children.addValueInput(
            "supportShellWallThickness",
            "Shell wall thickness",
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(self.options.supportShellWallThickness),
        )

        # Save, restore and erase defaults
        persistGroup = self.inputs.addGroupCommandInput("persistGroup", "Defaults")
        persistGroup.isExpanded = True
        restoreDefaultsInput = persistGroup.children.addBoolValueInput(Actions.RESTORE_DEFAULTS.name, "Reset", False, "", False)
        restoreDefaultsInput.text = "Reset all inputs to default values"
        saveDefaultsInput = persistGroup.children.addBoolValueInput(Actions.SAVE_DEFAULTS.name, "Update defaults", False, "", False)
        saveDefaultsInput.text = "Save current input values as new defaults"
        eraseDefaultsInput = persistGroup.children.addBoolValueInput(Actions.ERASE_DEFAULTS.name, "Factory reset", False, "", False)
        eraseDefaultsInput.text = "Erase saved input value defaults"

        message = 'Does this add-in save you time? Say thanks by <a href="https://buymeacoffee.com/benalman">buying me a coffee.</a>'
        coffeeTextBox = self.inputs.addTextBoxCommandInput("coffeeTextBox", "Thanks", message, 1, True)
        coffeeTextBox.isFullWidth = True
