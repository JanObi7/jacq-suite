import sys, os, json
from PySide6.QtWidgets import QLineEdit, QPushButton, QApplication, QLabel, QFormLayout, QComboBox, QDialog, QFileDialog, QToolBar, QMainWindow, QMessageBox, QWidget, QSizePolicy, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QBrush, QPen, QColor

import scan, stamp
from project import Project

class ImageLabel(QLabel):

  def __init__(self, parent=None):
    super(ImageLabel, self).__init__(parent)
    self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Ignored)
    self.image = None

  def loadImage(self, filename, dx, dy):
    self.image = QPixmap(filename)
    self.dx = dx
    self.dy = dy
    self.showImage()

  def showImage(self):
    if self.image:
      wi = self.image.width()*self.dy
      hi = self.image.height()*self.dx

      wv = self.width()-100
      hv = self.height()-100

      if wi/hi >= wv/hv:
        w = wv
        h = hi*wv/wi
      else:
        w = wi*hv/hi
        h = hv

      self.setPixmap(self.image.scaled(w,h,Qt.AspectRatioMode.IgnoreAspectRatio))

  def resizeEvent(self, event):
    self.showImage()
    return super().resizeEvent(event)
  


class MainWindow(QMainWindow):

  def __init__(self, parent=None):
      super(MainWindow, self).__init__(parent)

      self.resize(1100,600)
      self.setWindowTitle("JacqSuite")
      self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'assets', 'JacqSuite.ico')))

      new_action = QAction(QIcon('./src/assets/folder_new.png'), 'Muster erstellen', self)
      new_action.triggered.connect(self.newProject)
      
      load_action = QAction(QIcon('./src/assets/open.png'), 'Muster laden', self)
      load_action.triggered.connect(self.openProject)
      
      edit_action = QAction(QIcon('./src/assets/edit.png'), 'Patrone erstellen', self)
      edit_action.triggered.connect(self.configPattern)
      
      scan_action = QAction(QIcon('./src/assets/scanner.png'), 'Patrone digitalisieren', self)
      scan_action.triggered.connect(self.scanPattern)
      
      pattern_action = QAction(QIcon('./src/assets/printer.png'), 'Patrone ausgeben', self)
      pattern_action.triggered.connect(self.renderPattern)
      
      config_action = QAction(QIcon('./src/assets/cogs.png'), 'Karten konfigurieren', self)
      config_action.triggered.connect(self.configProgram)
      
      card_action = QAction(QIcon('./src/assets/punch-card.png'), 'Karten erstellen', self)
      card_action.triggered.connect(self.generateCards)
      
      exit_action = QAction(QIcon('./src/assets/exit-button.png'), 'Programm beenden', self)
      exit_action.triggered.connect(self.close)
      
      stamp_action = QAction(QIcon('./src/assets/locher.png'), 'Karten stanzen', self)
      stamp_action.triggered.connect(self.stampCards)
      
      weave_action = QAction(QIcon('./src/assets/webstuhl.png'), 'Stoffe weben', self)
      # weave_action.triggered.connect(self.stampCards)

      spacer = QWidget()
      spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

      toolbar = QToolBar('Main ToolBar')
      toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
      toolbar.setIconSize(QSize(64, 64))
      self.addToolBar(toolbar)

      toolbar.addAction(new_action)
      toolbar.addAction(load_action)
      toolbar.addSeparator()
      toolbar.addAction(edit_action)
      toolbar.addAction(scan_action)
      toolbar.addAction(pattern_action)
      toolbar.addSeparator()
      toolbar.addAction(config_action)
      toolbar.addAction(card_action)
      toolbar.addAction(stamp_action)
      toolbar.addSeparator()
      toolbar.addAction(weave_action)
      toolbar.addWidget(spacer)
      toolbar.addAction(exit_action)

      self.image = ImageLabel()
      self.setCentralWidget(self.image)

      self.loadConfig()
      if self.config["path"]:
        self.project = Project(self.config["path"])
        self.updateView()
      else:
        self.openProject()

  def showMessage(self, title, text):
    msgBox = QMessageBox(self)
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec();

  def updateView(self):
    if self.project:
      self.setWindowTitle("JacqSuite - " + self.project.path)

      self.image.loadImage(self.project.path + "/design.png", self.project.config["design"]["dx"], self.project.config["design"]["dy"])


  # Greets the user
  def newProject(self):
    path = QFileDialog.getExistingDirectory(self, "Leeren Ordner auswählen", ".", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      self.config["path"] = path
      self.saveConfig()
      self.project = Project(path)
      self.configPattern()
      self.updateView()

  def openProject(self):
    path = QFileDialog.getExistingDirectory(self, "Ordner auswählen", "./data", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      self.config["path"] = path
      self.saveConfig()
      self.project = Project(path)
      self.updateView()

  def configPattern(self):
    dialog = QDialog(self)
    dialog.setMinimumWidth(200)
    layout = QFormLayout()

    nk = QLineEdit(str(self.project.config["design"]["width"]))
    ns = QLineEdit(str(self.project.config["design"]["height"]))
    div = QComboBox()
    div.addItems(["4-16", "5-16", "6-16", "6-20", "7-12", "7-16", "8-18", "9-8", "10-12"])
    div.setCurrentText(str(self.project.config["design"]["dy"]) + "-" + str(self.project.config["design"]["dx"]))

    def save():
      self.project.config["design"]["width"] = int(nk.text())
      self.project.config["design"]["height"] = int(ns.text())
      self.project.config["design"]["dx"] = int(div.currentText().split("-")[1])
      self.project.config["design"]["dy"] = int(div.currentText().split("-")[0])
      self.project.saveConfig()

      self.project.initDesign()
      self.project.saveDesign()

      dialog.close()

      self.renderPattern()
      self.updateView()

    ok = QPushButton("erstellen")
    ok.pressed.connect(save)

    layout.addRow("Anzahl Ketten:", nk)
    layout.addRow("Anzahl Schüsse:", ns)
    layout.addRow("Teilung:", div)
    layout.addWidget(ok)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Patrone erstellen")

    dialog.exec()

  def configProgram(self):
    dialog = QDialog(self)
    dialog.setMinimumWidth(200)
    layout = QFormLayout()

    nk = QLineEdit(str(self.project.config["program"]["nk"]))
    ns = QLineEdit(str(self.project.config["program"]["ns"]))

    rule = QComboBox()
    rule.addItems(["1x1-R1-red"])
    rule.setCurrentText(self.project.config["program"]["rule"])

    config = QComboBox()
    config.addItems(["2x880"])
    config.setCurrentText(self.project.config["program"]["config"])

    def save():
      self.project.config["program"]["nk"] = int(nk.text())
      self.project.config["program"]["ns"] = int(ns.text())
      self.project.config["program"]["rule"] = rule.currentText()
      self.project.config["program"]["config"] = config.currentText()
      self.project.saveConfig()

      dialog.close()

      self.updateView()

    ok = QPushButton("übernehmen")
    ok.pressed.connect(save)

    layout.addRow("Anzahl Ketten:", nk)
    layout.addRow("Anzahl Schüsse:", ns)
    layout.addRow("Regel:", rule)
    layout.addRow("Karten:", config)
    layout.addWidget(ok)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Karten konfigurieren")

    dialog.exec()

  def scanPattern(self):
    self.win = scan.MainWindow(self.project)
    self.win.showMaximized()

  def renderPattern(self):
    self.project.renderDesign()
    # self.showMessage("Patrone ausgeben", "Die Patrone wurde erstellt und ausgegeben.")
    self.updateView()

  def generateCards(self):
    self.project.buildProgram()
    self.project.renderProgram()
    self.project.generateCards()
    self.showMessage("Karten erstellt", "Die Karten wurden erstellt und ausgegeben.")

  def stampCards(self):
    cards = self.project.readCards()
    self.win = stamp.CardStamper(cards)
    self.win.show()

  def loadConfig(self):
    if os.path.exists("config.json"):
      with open("config.json", "r") as file:
        self.config = json.load(file)
    else:
      self.config = {
        "path": None
      }
      self.saveConfig()
    
  def saveConfig(self):
    with open("config.json", "w") as file:
      json.dump(self.config, file, indent=2)


if __name__ == '__main__':
  app = QApplication(sys.argv)
  win = MainWindow()
  win.show()
  sys.exit(app.exec())