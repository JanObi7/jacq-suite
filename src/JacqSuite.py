import numpy as np
import cv2 as cv
import json
import sys, os

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QFileDialog, QTabWidget, QGridLayout
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


#############################################################################
class MainWindow(QtWidgets.QMainWindow):

  def __init__(self):
    super().__init__()

    # data
    if config["last_project"]:
      self.fabric = Fabric(config["last_project"])
    else:
      self.fabric = None

    self.resize(640,400)
    self.setWindowTitle("JacqSuite")
    self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'JacqSuite.ico')))

    self.tab1 = QtWidgets.QWidget()
    self.tab1.setLayout(QtWidgets.QGridLayout())

    tabs = QTabWidget()
    tabs.addTab(self.tab1, "Ausschnitte")
    self.setCentralWidget(tabs)


    actionNew = QtGui.QAction("neu ...", self)
    actionNew.setStatusTip("ein neues Projekt anlegen")
    actionNew.triggered.connect(self.newProject)

    actionOpen = QtGui.QAction("öffnen ...", self)
    actionOpen.setStatusTip("ein bestehendes Projekt zur Bearbeitung öffnen")
    actionOpen.triggered.connect(self.openProject)

    actionClose = QtGui.QAction("schließen", self)
    actionClose.setStatusTip("aktuelles Projekt schließen")
    actionClose.triggered.connect(self.closeProject)

    actionEditPattern = QtGui.QAction("bearbeiten", self)
    actionEditPattern.setStatusTip("Muster bearbeiten")
    actionEditPattern.triggered.connect(self.fabric.editPattern)

    actionRenderPattern = QtGui.QAction("ausgeben", self)
    actionRenderPattern.setStatusTip("Muster in Datei ausgeben")
    actionRenderPattern.triggered.connect(self.fabric.renderPattern)

    actionInitPattern = QtGui.QAction("zurücksetzen", self)
    actionInitPattern.setStatusTip("Muster löschen")
    actionInitPattern.triggered.connect(self.fabric.initPattern)

    actionGenerateCards = QtGui.QAction("ausgeben", self)
    actionGenerateCards.setStatusTip("Karten erzeugen")
    actionGenerateCards.triggered.connect(self.fabric.generateCards)

    actionRenderTexture = QtGui.QAction("ausgeben", self)
    actionRenderTexture.setStatusTip("Textur in Datei ausgeben")
    actionRenderTexture.triggered.connect(self.fabric.renderTexture)


    menubar = self.menuBar()
    project = QtWidgets.QMenu("Projekt")
    project.addAction(actionOpen)
    project.addAction(actionClose)
    menubar.addMenu(project)

    pattern = QtWidgets.QMenu("Muster")
    pattern.addAction(actionEditPattern)
    pattern.addAction(actionRenderPattern)
    pattern.addSeparator()
    pattern.addAction(actionInitPattern)
    menubar.addMenu(pattern)

    cards = QtWidgets.QMenu("Karten")
    cards.addAction(actionGenerateCards)
    menubar.addMenu(cards)

    menu = QtWidgets.QMenu("Texturen")
    menu.addAction(actionRenderTexture)
    menubar.addMenu(menu)

    self.updateViews()

  def updateViews(self):
    if self.fabric:
      self.setWindowTitle("JacqSuite - " + self.fabric.path)

      layout = self.tab1.layout()
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
        layout.addWidget(digit, i,3)
        edit = QtWidgets.QPushButton("Bearbeiten")
        layout.addWidget(edit, i, 4)
        remove = QtWidgets.QPushButton("Löschen")
        layout.addWidget(remove, i, 5)

    else:
      self.setWindowTitle("JacqSuite")

      layout = self.tab1.layout()
      for i in reversed(range(layout.count())):
        widget = layout.itemAt(i).widget()
        layout.removeWidget(widget)
        widget.setParent(None)


  def newProject(self):
    path = QFileDialog.getExistingDirectory(self, "Ordner auswählen", ".", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    print(path)
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