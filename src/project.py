import os, json
import numpy as np
import cv2 as cv
import JacqPattern, JacqProgram

class Project:

  def __init__(self, path):
    self.path = path

    # init empty project
    if not os.path.exists(self.path+"/config.json"):
      self.create()
    else:
      self.load()

  def create(self):
    # create config
    self.config = {
      "general": {},
      "design": {
        "width": 10,
        "height": 10,
        "dx": 1,
        "dy": 1
      },
      "scans": [
      ],
      "program": {
        "nk": 1760,
        "ns": 36,
        "config": "2x880",
        "rule": "1-1-rapport-red"
      },
    }
    self.saveConfig()

    # create subdirs
    os.mkdir(self.path+"/pattern")
    os.mkdir(self.path+"/scans")
    os.mkdir(self.path+"/cards")
    os.mkdir(self.path+"/textures")

    # pattern
    self.initDesign()
    self.saveDesign()

    # scans
    self.loadScans()

  def load(self):
    self.loadConfig()
    self.loadDesign()
    self.loadScans()

  def loadConfig(self):
    with open(self.path+"/config.json", "r", encoding="utf-8") as fp:
      self.config = json.load(fp)

  def saveConfig(self):
    with open(self.path+"/config.json", "w", encoding="utf-8") as fp:
      json.dump(self.config, fp, indent=2)

  def initDesign(self, sample=None):
    # read config
    w = self.config["design"]["width"]
    h = self.config["design"]["height"]

    # create pattern
    self.design = np.zeros((h, w, 4), np.uint8)

    # empty undefined pattern
    self.design[:,:] = (255,255,255,0)

    # sample: strpes atlas binding
    red = (255,0,0,255)
    white = (255,255,255,255)
    if sample == "atlas":
      for k in range(w):
        if k % 16 >= 5:
          self.design[0:h,k:k+1] = white
        else:
          self.design[0:h,k:k+1] = red

      for s in range(h):
        for k in range(0, w, 16):
          ms = s % 5
          mk = int(k / 16) % 5
          if (ms, mk) in [(0,0), (2,1), (4,2), (1,3), (3,4)]:
            self.design[s,k+3] = white
            self.design[s,k+6] = red
            self.design[s,k+11] = red
          if (ms, mk) in [(1,0), (3,1), (0,2), (2,3), (4,4)]:
            self.design[s,k+0] = white
            self.design[s,k+9] = red
            self.design[s,k+14] = red
          if (ms, mk) in [(2,0), (4,1), (1,2), (3,3), (0,4)]:
            self.design[s,k+2] = white
            self.design[s,k+7] = red
            self.design[s,k+12] = red
          if (ms, mk) in [(3,0), (0,1), (2,2), (4,3), (1,4)]:
            self.design[s,k+4] = white
            self.design[s,k+5] = red
            self.design[s,k+10] = red
            self.design[s,k+15] = red
          if (ms, mk) in [(4,0), (1,1), (3,2), (0,3), (2,4)]:
            self.design[s,k+1] = white
            self.design[s,k+8] = red
            self.design[s,k+13] = red

  def loadDesign(self):
    filename = self.path+"/pattern/design.png"
    if os.path.exists(filename):
      self.design = cv.imread(filename, flags=cv.IMREAD_UNCHANGED)
      self.design = cv.cvtColor(self.design, cv.COLOR_BGRA2RGBA)

      # create frame mask
      z = 4
      w = self.config["design"]["width"]
      h = self.config["design"]["height"]
      dx = self.config["design"]["dx"]
      dy = self.config["design"]["dy"]
      m = 1
      self.mask = np.zeros((z*dx*h, z*dy*w), np.uint8)
      for y in range(h):
          for x in range(w):
              self.mask[z*dx*y+m:z*dx*y+z*dx-m, z*dy*x+m:z*dy*x+z*dy-m] = 255
      # cv.imshow("mask", cv.resize(self.mask, (400,800)))

    else:
      self.initDesign()
      self.saveDesign()

  def getDesign(self, framed, k1, k2, s1, s2):
    z = 4
    w = self.config["design"]["width"]
    h = self.config["design"]["height"]
    dx = self.config["design"]["dx"]
    dy = self.config["design"]["dy"]
    m = 2

    img = cv.resize(self.design, (z*dy*w, z*dx*h), interpolation=cv.INTER_NEAREST)

    if framed:
      for y in range(s1, s2+1):
          for x in range(k1, k2+1):
              img[z*dx*y+m:z*dx*y+z*dx-m, z*dy*x+m:z*dy*x+z*dy-m] = (0,0,0,0)

    return img


  def saveDesign(self):
    pattern = cv.cvtColor(self.design, cv.COLOR_RGBA2BGRA)
    cv.imwrite(self.path+"/pattern/design.png", pattern)

  def renderDesign(self):
    image = JacqPattern.render(self.design, self.config["design"]["dx"], self.config["design"]["dy"])
    cv.imwrite(self.path+"/pattern/design_full.png", image)

  def loadScans(self):
    z = 4
    nx = self.config["design"]["width"]
    ny = self.config["design"]["height"]
    dx = self.config["design"]["dx"]
    dy = self.config["design"]["dy"]
    self.scans = np.zeros((z*dx*ny, z*dy*nx, 3), np.uint8)

    for config in self.config["scans"]:
      filename = config["filename"]
      kmin = config["kmin"]
      kmax = config["kmax"]
      smin = config["smin"]
      smax = config["smax"]
      point_tl = config["point_tl"]
      point_tr = config["point_tr"]
      point_bl = config["point_bl"]
      point_br = config["point_br"]

      # read image
      scan = cv.imread(self.path+"/scans/"+filename, flags=cv.IMREAD_UNCHANGED)
      scan = cv.cvtColor(scan, cv.COLOR_BGR2RGB)

      # set scan points

      # convert and set points
      scan_points = [
        point_tl, point_tr,
        point_bl, point_br
      ]

      xmin = kmin-1
      xmax = kmax
      ymin = ny-smax
      ymax = ny-smin+1
      w = z*dy*(xmax-xmin)
      h = z*dx*(ymax-ymin)
      part_points = [
        [0,0], [w,0],
        [0,h], [w,h]
      ]

      # transform image
      matrix = cv.getPerspectiveTransform(np.float32(scan_points), np.float32(part_points))
      scan = cv.warpPerspective(scan, matrix, (w, h))


      self.scans[z*dx*ymin:z*dx*ymax, z*dy*xmin:z*dy*xmax] = scan
      # cv.imshow("scan", cv.resize(scan, (400,800)))

    # cv.imshow("debug", cv.resize(self.scans, (400,800)))

  def createScan(self):
    return {
      "filename": "...",
      "limit": 150,
      "kmin": 0,
      "kmax": 0,
      "smin": 0,
      "smax": 0,
      "point_tl": [0,0],
      "point_tr": [0,0],
      "point_bl": [0,0],
      "point_br": [0,0]
    }

  def insertScan(self, scan):
    self.config["scans"].append(scan)
    self.saveConfig()
    self.loadScans()

  def deleteScan(self, scan):
    self.config["scans"].remove(scan)
    self.saveConfig()
    self.loadScans()

  def buildProgram(self):
    red = (255,0,0,255)
    white = (255,255,255,255)

    w = self.config["design"]["width"]
    h = self.config["design"]["height"]
    rw = self.config["design"]["rw"]
    rh = self.config["design"]["rh"]
    rx = self.config["design"]["rx"]
    ry = self.config["design"]["ry"]

    nk = self.config["program"]["nk"]
    ns = self.config["program"]["ns"]
    dk = self.config["program"]["dk"]
    ds = self.config["program"]["ds"]


    self.program = np.zeros((ns, nk, 4), np.uint8)

    def getPattern(x, y):
      return tuple(self.design[h-1-(y%rh)-ry, x%rw+rx].tolist())

    def setProgram(k, s, color):
      self.program[ns-1-s, k] = color

    # rules
    def rule (color, x, y):
      if color == red:
        return red
      else:
        return white

    for k in range(nk):
      for s in range(ns):
        color = getPattern(k, s)

        setProgram(k, s, rule(color, k, s))

    cv.imwrite(self.path+"/pattern/program.png", cv.cvtColor(self.program, cv.COLOR_RGBA2BGRA))

  def renderProgram(self):
    nk = self.config["program"]["nk"]
    ns = self.config["program"]["ns"]
    dk = self.config["program"]["dk"]
    ds = self.config["program"]["ds"]
    image = JacqProgram.renderProgram(self.program, nk, ns, dk, ds)
    cv.imwrite(self.path+"/pattern/program_full.png", image)

if __name__ == '__main__':
  project = Project("c:/temp/jacq-suite/data/D2132")

  project.renderDesign()
  # project.buildProgram()
  # project.renderProgram()
  