import json, os

def readSetting(name, default=None):
  if os.path.exists("config.json"):
    with open("config.json", "r") as file:
      config = json.load(file)
      if name in config:
        return config[name]
  return default
  
def writeSetting(name, value):
  if os.path.exists("config.json"):
    with open("config.json", "r") as file:
      config = json.load(file)
  else:
    config = {}

  config[name] = value

  with open("config.json", "w") as file:
    json.dump(config, file, indent=2)

