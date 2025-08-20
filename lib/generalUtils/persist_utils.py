from os.path import normpath, join, dirname, abspath, exists
from os import mkdir, remove
import json
from ...lib import fusionAddInUtils as futil

persistDir = normpath(join(dirname(abspath(__file__)), '../../persist_defaults'))

class Persistable():
  def __init__(self, persistFile: str, defaults: dict):
    self.persistFile = join(persistDir, persistFile)
    self._defaults = defaults
    self.restoreDefaults()
  
  def saveDefaults(self):
    try:
      if not exists(persistDir):
        mkdir(persistDir)
      with open(self.persistFile, 'w') as persistFile:
        data = {}
        for key in self._defaults.keys():
          data[key] = getattr(self, key)
        json.dump(data, persistFile, indent=2)
        futil.log(f'saved defaults file {self.persistFile}')
      return True
    except:
      futil.log(f'error when attempting to save defaults file {self.persistFile}')
      return False

  def __loadDefaults(self):
    try:
      data = False
      if exists(self.persistFile):
        with open(self.persistFile) as persistFile:
          data = json.load(persistFile)
          futil.log(f'loaded defaults file {self.persistFile}')
      else:
        futil.log(f'no defaults file to load {self.persistFile}')
      return data
    except:
      futil.log(f'error when attempting to load defaults file {self.persistFile}')
      return False

  def restoreDefaults(self):
    data = self._defaults | (self.__loadDefaults() or {})
    for key, value in data.items():
      setattr(self, key, value)

  # Ensure invalid values loaded from persistFile don't break things
  def ensureDefaultKeyIsValid(self, keyName, obj):
    key = getattr(self, keyName)
    if not key in obj:
      futil.log(f'Warning: {keyName} "{key}" invalid, restoring default value "{self._defaults[keyName]}"')
      setattr(self, keyName, self._defaults[keyName])

  def eraseDefaults(self):
    try:
      if exists(self.persistFile):
        remove(self.persistFile)
        futil.log(f'erased defaults file {self.persistFile}')
      else:
        futil.log(f'no defaults file to erase {self.persistFile}')
      return True
    except:
      futil.log(f'error when attempting to erase defaults file {self.persistFile}')
      return False

