version = "0.1"

import numpy as np
import cv2 as cv
import json
import sys, os
from functools import partial

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import QSize, QPoint
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPainter, QColor, QBrush
from PySide6.QtWidgets import QFileDialog, QTabWidget, QGridLayout, QLineEdit, QPushButton, QFormLayout, QComboBox
from PySide6.QtWidgets import QVBoxLayout, QListWidget, QLabel, QWidget, QHBoxLayout, QMessageBox
import JacqScan, JacqPattern, JacqCard, JacqWeave
from views import PatternView

from project import Project


#############################################################################
class MainWindow(QtWidgets.QMainWindow):

  def __init__(self):
    super().__init__()

    self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'JacqSuite.ico')))

    menubar = self.menuBar()

    menu = menubar.addMenu("Projekt")
    menu.addAction("Neu", self.newProject)
    menu.addAction("Öffnen", self.openProject)
    menu.addSeparator()
    menu.addAction("Beenden", self.close)

    menu = menubar.addMenu("Muster")
    menu.addAction("Konfigurieren", self.initPattern)
    menu.addAction("Scans ...", self.editScans)
    menu.addAction("Ausgeben", self.renderPattern)

    menu = menubar.addMenu("Patrone")
    menu.addAction("Erstellen", self.buildProgram)
    menu.addAction("Ausgeben", self.renderProgram)
    menu.addSeparator()
    menu.addAction("Karten ausgeben", self.generateCards)
    menu.addAction("Karten stanzen", self.stampCards)
    menu.addSeparator()
    menu.addAction("Stoff ausgeben", self.renderTexture)

    # data
    if config["last_project"]:
      self.project = Project(config["last_project"])
    else:
      self.openProject()

    self.editor = PatternView(self, self.project)
    self.setCentralWidget(self.editor)

    self.updateViews()

  def closeEvent(self, event: QCloseEvent) -> None:
      self.project.saveDesign()

      return super().closeEvent(event)

  def updateViews(self):
      self.setWindowTitle(f"JacqSuite {version} - {self.project.path}")

      if hasattr(self, "editor"):
        self.editor.scene.updatePattern()
        self.project.loadScans()
        self.editor.scene.updateScans()

  def newProject(self):
    path = QFileDialog.getExistingDirectory(self, "Leeren Ordner auswählen", ".", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      config["last_project"] = path
      saveAppConfig()
      self.project = Project(path)
      self.initPattern()
      self.updateViews()
    
  def openProject(self):
    path = QFileDialog.getExistingDirectory(self, "Ordner auswählen", "./data", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if path:
      config["last_project"] = path
      saveAppConfig()
      self.project = Project(path)
      self.updateViews()

  def initPattern(self):
    dialog = QtWidgets.QDialog(self)
    layout = QFormLayout()

    nk = QLineEdit(str(self.project.config["design"]["width"]))
    ns = QLineEdit(str(self.project.config["design"]["height"]))
    div = QComboBox()
    div.addItems(["4-16", "5-16", "6-20", "7-12", "7-16", "10-12"])
    div.setCurrentText(str(self.project.config["design"]["dy"]) + "-" + str(self.project.config["design"]["dx"]))

    sample = QComboBox()
    sample.addItems(["-", "atlas"])
    sample.setCurrentText("-")

    def save():
      self.project.config["design"]["width"] = int(nk.text())
      self.project.config["design"]["height"] = int(ns.text())
      self.project.config["design"]["dx"] = int(div.currentText().split("-")[1])
      self.project.config["design"]["dy"] = int(div.currentText().split("-")[0])
      self.project.saveConfig()

      self.project.initDesign(sample=sample.currentText())
      self.project.saveDesign()

      dialog.close()

      self.updateViews()


    ok = QPushButton("OK")
    ok.pressed.connect(save)

    layout.addRow("Anzahl Ketten:", nk)
    layout.addRow("Anzahl Schüsse:", ns)
    layout.addRow("Teilung:", div)
    layout.addRow("Muster:", sample)
    layout.addWidget(ok)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Muster festlegen")

    dialog.exec()

  def editScans(self):
    dialog = QtWidgets.QDialog(self)

    scans = QListWidget()

    def updateScans():
      scans.clear()
      for scan in self.project.config["scans"]:
        scans.addItem(f"{scan["filename"]}: K: {scan["kmin"]} .. {scan["kmax"]}, S: {scan["smin"]} .. {scan["smax"]}")

    def createScan():
      scan = self.project.createScan()
      self.editScan(scan)
      self.project.insertScan(scan)
      updateScans()

    def deleteScan():
      idx = scans.currentRow()
      scan = self.project.config["scans"][idx]
      self.project.deleteScan(scan)
      updateScans()

    def openScan():
      idx = scans.currentRow()
      scan = self.project.config["scans"][idx]
      self.editScan(scan)
      updateScans()

    btn_add = QPushButton("hinzufügen")
    btn_add.pressed.connect(createScan)
    btn_edit = QPushButton("bearbeiten")
    btn_edit.pressed.connect(openScan)
    btn_remove = QPushButton("löschen")
    btn_remove.pressed.connect(deleteScan)
    btn_ok = QPushButton("OK")
    btn_ok.pressed.connect(dialog.close)

    layout1 = QVBoxLayout()
    layout1.addWidget(btn_add)
    layout1.addWidget(btn_edit)
    layout1.addWidget(btn_remove)
    layout1.addWidget(btn_ok)

    layout = QHBoxLayout()
    layout.addWidget(scans)
    layout.addLayout(layout1)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Scans bearbeiten")

    updateScans()

    dialog.exec()

    self.updateViews()

  def showMessage(self, title, text):
    msgBox = QMessageBox(self)
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec();

  def renderPattern(self):
    self.project.renderDesign()
    self.showMessage("Muster ausgeben", "Das Muster wurde ausgegeben.")

  def generateCards(self):
    self.project.generateCards()
    self.showMessage("Karten ausgegeben", "Die Karten wurden ausgegeben.")

  def stampCards(self):
    cards = JacqCard.readCards(self.project.path)
    dialog = StampDialog(self, cards)
    dialog.exec()

  def renderTexture(self):
    self.project.renderTexture()

  def buildProgram(self):
    self.project.buildProgram()
    self.showMessage("Patrone erstellt", "Die Patrone wurde erstellt.")

  def renderProgram(self):
    self.project.renderProgram()
    self.showMessage("Patrone ausgeben", "Die Patrone wurde ausgegeben.")

  def editScan(self, scan):
    
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
      self.project.saveConfig()

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
      pathname, _ = QFileDialog.getOpenFileName(caption="Scan auswählen", dir=self.project.path+"/scans")
      if pathname:
        scan["filename"] = os.path.basename(pathname)
        filename.setText(scan["filename"])

    def tl_pressed():
      scan["point_tl"] = JacqScan.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_tl.setText(str(scan["point_tl"]))

    def tr_pressed():
      scan["point_tr"] = JacqScan.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_tr.setText(str(scan["point_tr"]))

    def bl_pressed():
      scan["point_bl"] = JacqScan.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_bl.setText(str(scan["point_bl"]))

    def br_pressed():
      scan["point_br"] = JacqScan.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
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
  win.showMaximized()
  app.exec()
  saveAppConfig()