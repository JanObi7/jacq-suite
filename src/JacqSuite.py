import numpy as np
import cv2 as cv
import json

import JacqScan, JacqPattern, JacqCard, JacqWeave

class Fabric:

  def __init__(self, path):
    self.path = path
    self.loadConfig()

  def loadConfig(self):
    with open(self.path+"/config.json", "r", encoding="utf-8") as fp:
      self.config = json.load(fp)

  def saveConfig(self):
    with open(self.path+"/config.json", "w", encoding="utf-8") as fp:
      json.dump(self.config, fp, indent=2)

  def initPattern(self, sample=None):
    # read config
    nk = self.config["pattern"]["nk"]
    ns = self.config["pattern"]["ns"]

    # create pattern
    self.pattern = np.zeros((ns, nk), np.uint8)

    # empty undefined pattern
    self.pattern[:,:] = 127

    # sample: strpes atlas binding
    if sample == "atlas":
      for k in range(nk):
        if k % 16 >= 5:
          self.pattern[0:ns,k:k+1] = 255
        else:
          self.pattern[0:ns,k:k+1] = 0

      for s in range(ns):
        for k in range(0, nk, 16):
          ms = s % 5
          mk = int(k / 16) % 5
          if (ms, mk) in [(0,0), (2,1), (4,2), (1,3), (3,4)]:
            self.pattern[s,k+3] = 255
            self.pattern[s,k+6] = 0
            self.pattern[s,k+11] = 0
          if (ms, mk) in [(1,0), (3,1), (0,2), (2,3), (4,4)]:
            self.pattern[s,k+0] = 255
            self.pattern[s,k+9] = 0
            self.pattern[s,k+14] = 0
          if (ms, mk) in [(2,0), (4,1), (1,2), (3,3), (0,4)]:
            self.pattern[s,k+2] = 255
            self.pattern[s,k+7] = 0
            self.pattern[s,k+12] = 0
          if (ms, mk) in [(3,0), (0,1), (2,2), (4,3), (1,4)]:
            self.pattern[s,k+4] = 255
            self.pattern[s,k+5] = 0
            self.pattern[s,k+10] = 0
            self.pattern[s,k+15] = 0
          if (ms, mk) in [(4,0), (1,1), (3,2), (0,3), (2,4)]:
            self.pattern[s,k+1] = 255
            self.pattern[s,k+8] = 0
            self.pattern[s,k+13] = 0

    # save pattern
    self.savePattern()

  def loadPattern(self):
    self.pattern = np.loadtxt(self.path+"/pattern/pattern.csv", np.uint8, delimiter=';')

  def savePattern(self):
    np.savetxt(self.path+"/pattern/pattern.csv", self.pattern, delimiter=';', fmt='%u')

  def renderPattern(self):
    self.loadPattern()
    image = JacqPattern.render(self.pattern, self.config["pattern"]["dk"], self.config["pattern"]["ds"])
    cv.imwrite(self.path+"/pattern/pattern.png", image)
    cv.imwrite(self.path+"/pattern/pattern_plain.png", self.pattern)

  def editPattern(self):
    self.loadPattern()
    self.pattern = JacqPattern.edit(self.pattern, self.config["pattern"]["dk"], self.config["pattern"]["ds"])
    self.savePattern()

  def createScan(self):
    scan = {
      "filename": "...",
      "kmin": 0,
      "kmax": 0,
      "smin": 0,
      "smax": 0,
      "point_tl": [0,0],
      "point_tr": [0,0],
      "point_bl": [0,0],
      "point_br": [0,0]
    }
    self.config["scans"].append(scan)
    self.saveConfig()
    return len(self.config["scans"])-1

  def deleteScan(self, idx):
    self.config["scans"].pop(idx)
    self.saveConfig()

  def digitizeScan(self, idx):
    self.loadPattern()

    part = self.config["scans"][idx]

    scan = cv.imread(self.path+"/scans/"+part["filename"])
    points = [part["point_tl"], part["point_tr"], part["point_bl"], part["point_br"]]

    self.pattern = JacqScan.Digitizer().run(self.pattern, scan, points, part["kmin"], part["kmax"], part["smin"], part["smax"], self.config["pattern"]["dk"], self.config["pattern"]["ds"])

    self.savePattern()

  def generateCards(self):
    JacqCard.buildCards(self.path)
    JacqCard.renderCards(self.path)

  def renderTexture(self):
    self.loadPattern()
    texture = JacqWeave.render(self.pattern, self.config["pattern"]["dk"], self.config["pattern"]["ds"])
    cv.imwrite(self.path+"/textures/texture.png", texture)