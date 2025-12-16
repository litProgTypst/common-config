
import copy
import os
from pathlib import Path
import sys
import traceback
import yaml

cacheDirs = [
  'bib',
  'html',
  'markdown',
  'pdf',
  'svg',
  'metaData',
  'lpit',
  'sha256sums',
  'webSite',
]

def die(msg) :
  print(msg)
  sys.exit(1)

def mergeConfig(config, newConfig, thePath) :
  """ This is a generic Python merge. It is a *deep* merge and handles
  recursive dictionary structures """

  # check to ensure both the yamlData and newYamlData are consistent.
  if type(config) is None :
    print("ERROR(mergeConfig): config data should NEVER be None ")
    print(f"ERROR(megeConfig): Stopped merge at {thePath}")
    return

  if type(config) != type(newConfig) :  # noqa
    print(f"ERROR(mergeConfig): Incompatible types {type(config)} and {type(newConfig)} while trying to merge config data at {thePath}")  # noqa
    print(f"ERROR(mergeConfig): Stopped merge at {thePath}")
    return

  # perform the merge at the same time expanding any '~' and '$baseDir' in
  # paths (strings).
  if type(newConfig) is dict :
    for key, value in newConfig.items() :
      if isinstance(value, str) :
        if value.startswith('~') :
          value = os.path.expanduser(value)
        config[key] = value
      elif isinstance(value, dict) :
        if key not in config :
          config[key] = {}
        mergeConfig(config[key], value, thePath + '.' + key)
      else :
        config[key] = copy.deepcopy(value)
  else :
    print("ERROR(mergeConfig): Config MUST be a dictionary.")
    print(f"ERROR(mergeConfig): Stopped merge at {thePath}")
    return

########################################################################
# ArgParse helper

def addConfigurationArgs(parser) :
  parser.add_argument(
    '-c', '--config',
    help="The path to the user configuration directory",
    default=os.path.expanduser('~/.config/lpit')
  )
  parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    default=False,
    action='store_true'
  )

########################################################################
# LpitConfig class

class LpitConfig(object) :
  def __new__(cls) :
    if not hasattr(cls, 'instance') :
      cls.instance = super(LpitConfig, cls).__new__(cls)
    return cls.instance

  def __getitem__(self, key) :
    return self.config[key]

  def __contains__(self, key) :
    return key in self.config

  def __setitem__(self, key, value) :
    self.config[key] = value

  def print(self) :
    print("-------------------------------------------------")
    print(yaml.dump(self.config))
    print("-------------------------------------------------")

  def addCacheDirs(self) :
    cachePath = Path('~/.cache/lpit')
    if 'cacheDir' in self.config :
      cachePath = Path(self.config['cacheDir'])
    cachePath = cachePath.expanduser()
    if not cachePath.exists() :
      cachePath.mkdir(parents=True, exist_ok=True)
    self.cacheDir = cachePath
    self.config['cacheDir'] = str(cachePath)

    for aDir in cacheDirs :
      theAttr = aDir + 'Cache'
      thePath = cachePath / aDir
      self.__setattr__(theAttr, thePath)
      if not thePath.exists() :
        thePath.mkdir(parents=True, exist_ok=True)

  def checkDirs(self) :
    if 'documentDirs' not in self.config :
      die("No document directories specified... nothing to do!")
    docDirs = self.config['documentDirs']

    if len(docDirs) < 1 :
      die("No document directories specified... nothing to do!")

    for aDir in docDirs :
      # here be dragons!
      aDirPath = Path(aDir).expanduser()
      if not aDirPath.exists() :
        aDirPath.mkdir(parents=True, exist_ok=True)

  def initConfigFromArgs(self, args) :
    self.configPath = Path(args['config']).expanduser()

    if not self.configPath.parent.exists() :
      self.configPath.parent.mkdir(parents=True, exist_ok=True)

    self.config = {}

  def mergeConfigFrom(self, aConfigFileName) :
    try :
      mergeConfigPath = self.configPath / aConfigFileName
      newConfig = yaml.safe_load(mergeConfigPath.read_text())
      if isinstance(newConfig, dict) and newConfig :
        mergeConfig(self.config, newConfig, '')
    except Exception as err :
      print(f"Could not merge configuration from {aConfigFileName} in {self.configPath}")  # noqa
      print(repr(err))
      print(traceback.format_exc())

  def finishedLoading(self, args, verbose=False) :
    self.addCacheDirs()

    for aKey, aValue in args.items() :
      if aValue : self.config[aKey] = aValue

    if 'projects' not in self.config :
      self.config['projects'] = {}

    if 'verbose' not in self.config :
      self.config['verbose'] = verbose

    if self.config['verbose'] : self.print()

########################################################################
# LPiT.YAML loading

localLpitYamlPath = Path('lpit.yaml')

def loadLpitYaml(docDir=None) :
  lpitYamlPath = Path(str(localLpitYamlPath))
  if docDir :
    lpitYamlPath = docDir / str(localLpitYamlPath)
  lpitYamlPath = lpitYamlPath.expanduser()

  lpitDef = {}
  try :
    lpitDef = yaml.safe_load(lpitYamlPath.read_text())

    if 'packages' not in lpitDef : lpitDef['packages'] = []

    # if lpitDef :
    #   print(yaml.dump(lpitDef))
  except FileNotFoundError :
    return {}
  except Exception as err :
    print("Could not load the document's lpit.yaml file")
    print(repr(err))
    sys.exit(1)

  if 'docOrderPriority' not in lpitDef :
    lpitDef['docOrderPriority'] = 0

  if 'doc' not in lpitDef :
    return lpitDef

  lpitDoc = lpitDef['doc']
  if 'name' not in lpitDoc :
    if 'id' not in lpitDoc :
      die("No doc:id specified in the `lpit.yaml` file")
    lpitDoc['name'] = lpitDoc['id']
    if '-' in lpitDoc['name'] :
      lpitDoc['name'] = lpitDoc['name'].split('-')[1]

  return lpitDef

