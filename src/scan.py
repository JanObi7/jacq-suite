version = "0.1"

import numpy as np
import cv2 as cv
import os

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPainter, QColor, QBrush, QIcon, QAction
from PySide6.QtWidgets import QFileDialog, QTabWidget, QGridLayout, QLineEdit, QPushButton, QFormLayout, QComboBox, QToolBar, QMainWindow, QDialog, QSizePolicy, QSlider, QSpinBox
from PySide6.QtWidgets import QVBoxLayout, QListWidget, QLabel, QWidget, QHBoxLayout, QMessageBox, QStackedLayout
from views import PatternView, PointSelector

#############################################################################
class MainWindow(QMainWindow):

  def __init__(self, project):
    super().__init__()

    self.setWindowIcon(QIcon('./assets/JacqSuite.ico'))
    self.setWindowTitle(f"JacqSuite")

    scans_action = QAction(QIcon('./assets/scans.png'), 'Scans konfigurieren', self)
    scans_action.triggered.connect(self.editScans)

    bright_action = QAction(QIcon('./assets/brightness.png'), 'Erkennung anpassen', self)
    bright_action.triggered.connect(self.editBrightness)

    close_action = QAction(QIcon('./assets/close.png'), 'Bearbeitung beenden', self)
    close_action.triggered.connect(self.close)

    toolbar = QToolBar('Main ToolBar')
    toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    toolbar.setIconSize(QSize(64, 64))
    self.addToolBar(toolbar)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


    toolbar.addAction(scans_action)
    toolbar.addAction(bright_action)
    toolbar.addWidget(spacer)
    toolbar.addAction(close_action)

    # data
    self.project = project

    self.editor = PatternView(self, self.project)
    self.setCentralWidget(self.editor)

    self.updateViews()

  def closeEvent(self, event: QCloseEvent) -> None:
      self.project.saveDesign()

      return super().closeEvent(event)

  def updateViews(self):
      self.setWindowTitle(f"JacqSuite - {self.project.path}")

      if hasattr(self, "editor"):
        self.editor.scene.updatePattern()
        self.project.loadScans()
        self.editor.scene.updateScans()

  def initPattern(self):
    dialog = QDialog(self)
    layout = QFormLayout()

    nk = QLineEdit(str(self.project.config["design"]["width"]))
    ns = QLineEdit(str(self.project.config["design"]["height"]))
    div = QComboBox()
    div.addItems(["4-16", "5-16", "6-16", "6-20", "7-12", "7-16", "8-18", "9-8", "10-12"])
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
    dialog = QDialog(self)

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

  def editScan(self, scan):
    
    dialog = QDialog(self)
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
      scan["point_tl"] = self.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_tl.setText(str(scan["point_tl"]))

    def tr_pressed():
      scan["point_tr"] = self.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_tr.setText(str(scan["point_tr"]))

    def bl_pressed():
      scan["point_bl"] = self.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_bl.setText(str(scan["point_bl"]))

    def br_pressed():
      scan["point_br"] = self.selectScanPoint(self.project.path+"/scans/"+scan["filename"])
      point_br.setText(str(scan["point_br"]))

    filename.pressed.connect(fn_pressed)  
    point_tl.pressed.connect(tl_pressed)
    point_tr.pressed.connect(tr_pressed)
    point_bl.pressed.connect(bl_pressed)
    point_br.pressed.connect(br_pressed)

    dialog.exec()

  def selectScanPoint_new(self, filename):
    dialog = QDialog(self)
    layout = QStackedLayout(dialog)

    selector = PointSelector(None, filename)
    layout.addWidget(selector)

    dialog.exec()

    return selector.scene.x, selector.scene.y

  def editBrightness(self):
    dialog = QDialog(self)
    dialog.setMinimumWidth(200)
    layout = QFormLayout()

    limit = QSpinBox()
    limit.setMinimum(120)
    limit.setMaximum(240)
    limit.setValue(self.editor.scene.limit)
    limit.setSingleStep(5)

    def save():
      self.editor.scene.limit = limit.value()
      print(self.editor.scene.limit)
      dialog.close()

    ok = QPushButton("speichern")
    ok.pressed.connect(save)

    layout.addRow("Helligkeitsschwelle:", limit)
    layout.addWidget(ok)

    dialog.setLayout(layout)
    dialog.setWindowTitle("Erkennung anpassen")

    dialog.exec()

  ###################################################################
  def selectScanPoint(self, pathname):
    stage = 0
    xs = 0
    ys = 0
    xmin = 0
    xmax = 0
    ymin = 0
    ymax = 0


    def mouse_event(event,x,y,flags,param):
      nonlocal stage, xs, ys, xmin, xmax, ymin, ymax

      if event == cv.EVENT_LBUTTONUP:
        if stage == 0:
          xs = 4*x
          ys = 4*y
          stage = 1
          update_view()

        elif stage == 1:
          xs = xmin+int(x/4)
          ys = ymin+int(y/4)
          stage = 2

    def update_view():
      nonlocal stage, xs, ys, xmin, xmax, ymin, ymax

      if stage == 0:
        scan = cv.imread(pathname)
        h, w, c = np.shape(scan)
        scan = cv.resize(scan, (int(w/4), int(h/4)))

      elif stage == 1:
        scan = cv.imread(pathname)
        h, w, c = np.shape(scan)

        xmin = xs-100 if xs-100 >= 0 else 0
        xmax = xs+100 if xs+100 < w else w
        ymin = ys-100 if ys-100 >= 0 else 0
        ymax = ys+100 if ys+100 < h else h

        scan = scan[ymin:ymax,xmin:xmax]
        scan = cv.resize(scan, (4*(xmax-xmin), 4*(ymax-ymin)))

      cv.imshow("scan", scan)

    cv.namedWindow('scan')
    cv.setMouseCallback('scan', mouse_event)

    update_view()

    while stage < 2:
      cv.waitKey(20)

    cv.destroyAllWindows()

    return [xs, ys]
