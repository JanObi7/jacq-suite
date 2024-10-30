version = "0.1"

import numpy as np
import cv2 as cv
import json
import sys, os
from functools import partial

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QFileDialog, QTabWidget, QGridLayout, QLineEdit, QPushButton, QFormLayout, QComboBox
import JacqScan, JacqPattern, JacqCard, JacqWeave

class Fabric:

  def __init__(self, path):
    self.path = path

    # init empty project
    if not os.path.exists(self.path+"/config.json"):
      # create config
      self.config = {
        "general": {},
        "pattern": {
          "nk": 0,
          "ns": 0,
          "dk": 16,
          "ds": 5
        },
        "scans": [
        ],
        "cards": {}
      }
      self.saveConfig()

      # create subdirs
      os.mkdir(path+"/pattern")
      os.mkdir(path+"/scans")
      os.mkdir(path+"/cards")
      os.mkdir(path+"/textures")

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

    self.pattern = JacqScan.Digitizer().run(self.pattern, scan, points, part["kmin"], part["kmax"], part["smin"], part["smax"], self.config["pattern"]["dk"], self.config["pattern"]["ds"], part["limit"])

    self.savePattern()

  def generateCards(self):
    JacqCard.buildCards(self.path)
    JacqCard.renderCards(self.path)

  def renderTexture(self):
    self.loadPattern()
    texture = JacqWeave.render(self.pattern, self.config["pattern"]["dk"], self.config["pattern"]["ds"])
    cv.imwrite(self.path+"/textures/texture.png", texture)


#############################################################################
class MainWindow(QtWidgets.QMainWindow):

  def __init__(self):
    super().__init__()

    # data
    if config["last_project"]:
      self.fabric = Fabric(config["last_project"])
    else:
      self.fabric = None

    actionQuit = QtGui.QAction("Beenden", self)
    actionQuit.triggered.connect(self.close)

    actionNew = QtGui.QAction("Muster Anlegen", self)
    actionNew.triggered.connect(self.newProject)

    actionOpen = QtGui.QAction("Muster Öffnen", self)
    actionOpen.triggered.connect(self.openProject)

    actionEditPattern = QtGui.QAction("Ausschnitte kopieren", self)
    actionEditPattern.triggered.connect(self.editPattern)

    actionRenderPattern = QtGui.QAction("Patrone Ausgeben", self)
    actionRenderPattern.triggered.connect(self.renderPattern)

    actionInitPattern = QtGui.QAction("Patrone Initialisieren", self)
    actionInitPattern.triggered.connect(self.initPattern)

    actionAddScan = QtGui.QAction("Ausschnitt hinzufügen", self)
    actionAddScan.triggered.connect(self.createScan)

    actionGenerateCards = QtGui.QAction("Karten Ausgeben", self)
    actionGenerateCards.triggered.connect(self.generateCards)

    actionRenderTexture = QtGui.QAction("Textur Ausgeben", self)
    actionRenderTexture.triggered.connect(self.renderTexture)

    self.resize(640,400)
    self.setWindowTitle(f"JacqSuite {version}")
    self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'JacqSuite.ico')))

    self.tab1 = QtWidgets.QWidget()
    toolbar = QtWidgets.QToolBar()
    toolbar.addAction(actionAddScan)
    toolbar.addAction(actionEditPattern)
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(toolbar)
    self.parts = QtWidgets.QWidget()
    self.parts.setLayout(QtWidgets.QGridLayout())
    layout.addWidget(self.parts)
    self.tab1.setLayout(layout)

    tabs = QTabWidget()
    tabs.addTab(self.tab1, "Ausschnitte")
    self.setCentralWidget(tabs)


    menubar = self.menuBar()
    project = QtWidgets.QMenu("Muster")
    project.addAction(actionNew)
    project.addAction(actionOpen)
    project.addSeparator()
    project.addAction(actionQuit)
    menubar.addMenu(project)

    pattern = QtWidgets.QMenu("Patrone")
    pattern.addAction(actionInitPattern)
    pattern.addAction(actionRenderPattern)
    menubar.addMenu(pattern)

    cards = QtWidgets.QMenu("Karten")
    cards.addAction(actionGenerateCards)
    menubar.addMenu(cards)

    menu = QtWidgets.QMenu("Textur")
    menu.addAction(actionRenderTexture)
    menubar.addMenu(menu)

    self.updateViews()

  def updateViews(self):
    if self.fabric:
      self.setWindowTitle(f"JacqSuite {version} - {self.fabric.path}")

      layout = self.parts.layout()
      for i in reversed(range(layout.count())):
        widget = layout.itemAt(i).widget()
        layout.removeWidget(widget)
        widget.setParent(None)

      for i in range(len(self.fabric.config["scans"])):
        scan = self.fabric.config["scans"][i]
        name = QtWidgets.QLabel(scan["filename"])
        layout.addWidget(name, i,1)
        ranges = QtWidgets.QLabel(f"K: {scan["kmin"]} .. {scan["kmax"]}, S: {scan["smin"]} .. {scan["smax"]}")
        layout.addWidget(ranges, i, 2)
        digit = QtWidgets.QPushButton("Digitalisieren")
        digit.pressed.connect(partial(self.digitizeScan, i))
        layout.addWidget(digit, i,3)
        edit = QtWidgets.QPushButton("Bearbeiten")
        edit.pressed.connect(partial(self.editScan, i))
        layout.addWidget(edit, i, 4)
        remove = QtWidgets.QPushButton("Löschen")
        remove.pressed.connect(partial(self.deleteScan, i))
        layout.addWidget(remove, i, 5)

    else:
      self.setWindowTitle(f"JacqSuite {version}")

      layout = self.parts.layout()
      for i in reversed(range(layout.count())):
        widget = layout.itemAt(i).widget()
        layout.removeWidget(widget)
        widget.setParent(None)


  def newProject(self):
    path = QFileDialog.getExistingDirectory(self, "Leeren Ordner auswählen", ".", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      config["last_project"] = path
      saveAppConfig()
      self.fabric = Fabric(path)
      self.initPattern()
      self.updateViews()
    
  def openProject(self):
    path = QFileDialog.getExistingDirectory(self, "Ordner auswählen", "./data", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      config["last_project"] = path
      saveAppConfig()
      self.fabric = Fabric(path)
      self.updateViews()

  def closeProject(self):
    if self.fabric:
      config["last_project"] = None
      saveAppConfig()
      self.fabric.saveConfig()
      self.fabric = None
      self.updateViews()

  def editPattern(self):
    self.fabric.editPattern()

  def initPattern(self):
    dialog = QtWidgets.QDialog(self)
    layout = QFormLayout()

    nk = QLineEdit(str(self.fabric.config["pattern"]["nk"]))
    ns = QLineEdit(str(self.fabric.config["pattern"]["ns"]))
    div = QComboBox()
    div.addItems(["4-16", "5-16"])
    div.setCurrentText(str(self.fabric.config["pattern"]["ds"]) + "-" + str(self.fabric.config["pattern"]["dk"]))

    def save():
      self.fabric.config["pattern"]["nk"] = int(nk.text())
      self.fabric.config["pattern"]["ns"] = int(ns.text())
      self.fabric.config["pattern"]["dk"] = int(div.currentText().split("-")[1])
      self.fabric.config["pattern"]["ds"] = int(div.currentText().split("-")[0])
      self.fabric.saveConfig()

      self.fabric.initPattern()

      dialog.close()

    ok = QPushButton("OK")
    ok.pressed.connect(save)

    layout.addRow("Anzahl Ketten:", nk)
    layout.addRow("Anzahl Schüsse:", ns)
    layout.addRow("Teilung:", div)
    layout.addWidget(ok)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Muster festlegen")

    dialog.exec()


  def renderPattern(self):
    self.fabric.renderPattern()

  def generateCards(self):
    self.fabric.generateCards()

  def renderTexture(self):
    self.fabric.renderTexture()

  def createScan(self):
    idx = self.fabric.createScan()
    self.updateViews()
    self.editScan(idx)

  def deleteScan(self, idx):
    self.fabric.deleteScan(idx)
    self.updateViews()

  def digitizeScan(self, idx):
    self.fabric.digitizeScan(idx)
    self.updateViews()

  def editScan(self, idx):
    scan = self.fabric.config["scans"][idx]

    dialog = QtWidgets.QDialog(self)
    layout = QGridLayout()

    filename = QPushButton(scan["filename"])
    limit = QLineEdit(str(scan["limit"]))
    kmin = QLineEdit(str(scan["kmin"]))
    kmax = QLineEdit(str(scan["kmax"]))
    smin = QLineEdit(str(scan["smin"]))
    smax = QLineEdit(str(scan["smax"]))
    point_tl = QPushButton(str(scan["point_tl"]))
    point_tr = QPushButton(str(scan["point_tr"]))
    point_bl = QPushButton(str(scan["point_bl"]))
    point_br = QPushButton(str(scan["point_br"]))

    def save():
      scan["limit"] = int(limit.text())
      scan["kmin"] = int(kmin.text())
      scan["kmax"] = int(kmax.text())
      scan["smin"] = int(smin.text())
      scan["smax"] = int(smax.text())
      self.fabric.saveConfig()

      self.updateViews()

      dialog.close()

    ok = QPushButton("OK")
    ok.pressed.connect(save)

    layout.addWidget(filename, 0, 0, 1, 2)
    layout.addWidget(limit, 0, 2)
    layout.addWidget(kmin, 2, 0)
    layout.addWidget(kmax, 2, 2)
    layout.addWidget(smin, 3, 1)
    layout.addWidget(smax, 1, 1)
    layout.addWidget(point_tl, 1, 0)
    layout.addWidget(point_tr, 1, 2)
    layout.addWidget(point_bl, 3, 0)
    layout.addWidget(point_br, 3, 2)
    layout.addWidget(ok, 4, 2, 1, 2)

    dialog.setLayout(layout)

    def fn_pressed():
      pathname, _ = QFileDialog.getOpenFileName(caption="Scan auswählen", dir=self.fabric.path+"/scans")
      if pathname:
        scan["filename"] = os.path.basename(pathname)
        filename.setText(scan["filename"])

    def tl_pressed():
      scan["point_tl"] = JacqScan.selectScanPoint(self.fabric.path+"/scans/"+scan["filename"])
      point_tl.setText(str(scan["point_tl"]))

    def tr_pressed():
      scan["point_tr"] = JacqScan.selectScanPoint(self.fabric.path+"/scans/"+scan["filename"])
      point_tr.setText(str(scan["point_tr"]))

    def bl_pressed():
      scan["point_bl"] = JacqScan.selectScanPoint(self.fabric.path+"/scans/"+scan["filename"])
      point_bl.setText(str(scan["point_bl"]))

    def br_pressed():
      scan["point_br"] = JacqScan.selectScanPoint(self.fabric.path+"/scans/"+scan["filename"])
      point_br.setText(str(scan["point_br"]))

    filename.pressed.connect(fn_pressed)  
    point_tl.pressed.connect(tl_pressed)
    point_tr.pressed.connect(tr_pressed)
    point_bl.pressed.connect(bl_pressed)
    point_br.pressed.connect(br_pressed)

    dialog.exec()


#############################################################################
config = {
  "last_project": None
}

def loadAppConfig():
  global config

  if os.path.exists("JacqSuite.config"):
    with open("JacqSuite.config", "r") as file:
      config = json.load(file)
  else:
    saveAppConfig()
  
def saveAppConfig():
  with open("JacqSuite.config", "w") as file:
    json.dump(config, file, indent=2)


if __name__ == '__main__':
  loadAppConfig()
  app = QtWidgets.QApplication(sys.argv)
  win = MainWindow()
  win.show()
  app.exec()
  saveAppConfig()