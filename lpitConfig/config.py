
import os
from pathlib import Path
import sys
import yaml

def die(msg) :
  print(msg)
  sys.exit(1)

########################################################################
# ArgParse helper

def addConfigurationArgs(parser) :
  parser.add_argument(
    '-c', '--config',
    help="The path to the user configuration file",
    default=os.path.expanduser('~/.config/lpitPublisher/config.yaml')
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
    cachePath = Path('~/.cache/lpitPublisher')
    if 'cacheDir' in self.config :
      cachePath = Path(self.config['cacheDir'])
    cachePath = cachePath.expanduser()
    if not cachePath.exists() :
      cachePath.mkdir(parents=True, exist_ok=True)
    self.cacheDir = cachePath
    self.config['cacheDir'] = str(cachePath)
    self.htmlCache     = cachePath / 'html'
    if not self.htmlCache.exists() :
      self.htmlCache.mkdir(parents=True, exist_ok=True)
    self.markdownCache = cachePath / 'markdown'
    if not self.markdownCache.exists() :
      self.markdownCache.mkdir(parents=True, exist_ok=True)
    self.pdfCache = cachePath / 'pdf'
    if not self.pdfCache.exists() :
      self.pdfCache.mkdir(parents=True, exist_ok=True)
    self.svgCache = cachePath / 'svg'
    if not self.svgCache.exists() :
      self.svgCache.mkdir(parents=True, exist_ok=True)
    self.metaDataCache = cachePath / 'metaData'
    if not self.metaDataCache.exists() :
      self.metaDataCache.mkdir(parents=True, exist_ok=True)
    self.lpitCache = cachePath / 'lpit'
    if not self.lpitCache.exists() :
      self.lpitCache.mkdir(parents=True, exist_ok=True)
    self.shaSumsCache = cachePath / 'sha256sums'
    if not self.shaSumsCache.exists() :
      self.shaSumsCache.mkdir(parents=True, exist_ok=True)
    self.webSiteCache = cachePath / 'webSite'
    if not self.webSiteCache.exists() :
      self.webSiteCache.mkdir(parents=True, exist_ok=True)

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

  def loadConfig(self, args, verbose=False) :
    configPath = Path(args['config']).expanduser()

    if not configPath.parent.exists() :
      configPath.parent.mkdir(parents=True, exist_ok=True)

    self.config = yaml.safe_load(configPath.read_text())
    if not self.config :
      self.config = {}

    for aKey, aValue in args.items() :
      if aValue : self.config[aKey] = aValue

    if 'verbose' not in self.config :
      self.config['verbose'] = verbose

    if 'monitor' not in self.config :
      self.config['monitor'] = ['*.typ' ]

    if 'formats' not in self.config :
      self.config['formats'] = [ 'metadata', 'html', 'svg', 'pdf' ]

    if 'webSiteName' not in self.config :
      self.config['webSiteName'] = 'LPiT Documents'

    self.checkDirs()
    self.addCacheDirs()

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

