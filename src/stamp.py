from PySide6.QtCore import QSize, QPoint, Qt
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPainter, QColor, QBrush, QPen, QKeyEvent, QIcon, QAction, QFont
from PySide6.QtWidgets import QMainWindow, QWidget, QSizePolicy, QToolBar, QMessageBox

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_analog_in_v3 import BrickletAnalogInV3

import time, math, os

from settings import readSetting, writeSetting
from card import scanStamp

#############################################################################
class Hardware:
  HOST = "localhost"
  PORT = 4223
  UID_S2 = "2cKV"
  UID_S1 = "2cKN"
  UID_IO = "27mU"
  UID_AI = "27eD"

  def __init__(self, callback):
    try:
      # read/init settings
      self.dmin = readSetting("dmin", [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80])
      self.dmax = readSetting("dmax", [180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180])

      # init tinkerforge
      self.ipcon = IPConnection() # Create IP connection
      self.ipcon.set_timeout(0.1)
      self.s1 = BrickletServoV2(self.UID_S1, self.ipcon) # Create device object
      self.s2 = BrickletServoV2(self.UID_S2, self.ipcon) # Create device object
      self.ai = BrickletAnalogInV3(self.UID_AI, self.ipcon) # Create device object
      self.ipcon.connect(self.HOST, self.PORT) # Connect to brickd

      self.mapping = [
        (self.s1, 9),
        (self.s1, 8),
        (self.s1, 7),
        (self.s1, 6),
        (self.s1, 3),
        (self.s1, 2),
        (self.s1, 1),
        (self.s1, 0),
        (self.s2, 9),
        (self.s2, 8),
        (self.s2, 7),
        (self.s2, 6),
        (self.s2, 3),
        (self.s2, 2),
        (self.s2, 1),
        (self.s2, 0),
      ]
      # configure and enable servos
      for i in range(16):
        s, p = self.mapping[i]
        s.set_pulse_width(p, 500, 2500)
        s.set_degree(p, 0, 180)
        s.set_motion_configuration(p, 500000, 500000, 500000)
        s.set_enable(p, True)    

      # configure ao
      self.calibration = False
      self.callback = callback
      self.voltage = 5000
      self.voltage_switch = readSetting("voltage_switch", 1100)
      self.voltage_max = readSetting("voltage_max", 1250)
      self.voltage_min = readSetting("voltage_min", 250)
      self.ai.register_callback(self.ai.CALLBACK_VOLTAGE, self.voltageEvent)
      self.ai.set_voltage_callback_configuration(10, True, 'x', 0, 5)

      print("hardware initialized")
      self.ready = True

      self.liftAll()

    except Exception as e:
      self.ready = False

      print(e)
      print("hardware not initialized")

  def close(self):
    self.liftAll()

    # disable servos
    try:
      for i in range(16):
        s, p = self.mapping[i]
        s.set_enable(p, False)
    except:
      pass

    # deinit tinkerforge
    try:
      self.ipcon.disconnect()
      print("hardware deinitialized")
    except:
      print("hardware not deinitialized")

  def voltageEvent(self, voltage):
    if self.calibration:
      if voltage < self.voltage_min:
        self.voltage_min = voltage
      if voltage > self.voltage_max:
        self.voltage_max = voltage
        self.voltage_switch = voltage-150
    else:
      if self.voltage < self.voltage_switch and voltage >= self.voltage_switch:
        print("voltage", voltage)
        self.callback()

    self.voltage = voltage


  def releaseAll(self):
    if self.ready:
      # release all
      for i in range(16):
        self.release(i)

      # wait for releasing
      time.sleep(1)

  def pressAll(self):
    if self.ready:
      # press all
      for i in range(16):
        self.press(i)

      # wait for releasing
      time.sleep(1)

  def liftAll(self):
    if self.ready:
      for i in range(16):
        self.lift(i)

      # wait for releasing
      time.sleep(1)

  def release(self, i):
    if self.ready:
      s, p = self.mapping[i]
      s.set_position(p, self.dmax[i])

  def press(self, i):
    if self.ready:
      s, p = self.mapping[i]
      s.set_position(p, self.dmin[i])

  def lift(self, i):
    if self.ready:
      s, p = self.mapping[i]
      s.set_position(p, 180)

  def reset(self):
    if self.ready:
      self.dmin = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
      self.dmax = [180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180]

      writeSetting("dmin", self.dmin)
      writeSetting("dmax", self.dmax)

      self.voltage_min = 250
      self.voltage_max = 1250
      self.voltage_switch = 1100

      writeSetting("voltage_min", self.voltage_min)
      writeSetting("voltage_max", self.voltage_max)
      writeSetting("voltage_switch", self.voltage_switch)

      self.releaseAll()
      time.sleep(1)

  def calibrate(self):
    if self.ready:
      self.dmin = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
      self.dmax = [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60]

      self.liftAll()
      time.sleep(1)

      for d in range(180,-1,-5):
        # drive to position
        for i in range(16):
          s, p = self.mapping[i]

          if self.dmin[i] == 0:
            s.set_position(p, d)
          else:
            s.set_position(p, self.dmax[i])

        # time to drive
        time.sleep(0.25)

        # measure current and calibrate
        for i in range(16):
          s, p = self.mapping[i]

          status = s.get_status()
          current = status.current[p]

          if current > 300:
            self.dmin[i] = d+10
            self.dmax[i] = min(d+70, 180)

      print("dmin", self.dmin)
      print("dmax", self.dmax)

      writeSetting("dmin", self.dmin)
      writeSetting("dmax", self.dmax)

      self.releaseAll()
      time.sleep(1)

  def calibratePoti(self):
    if self.ready:
      self.calibration = True
      self.voltage_max = 0
      self.voltage_min = 5000

      self.liftAll()
      time.sleep(10)

      self.calibration = False

      print(self.voltage_min, self.voltage_max)

      writeSetting("voltage_min", self.voltage_min)
      writeSetting("voltage_max", self.voltage_max)
      writeSetting("voltage_switch", self.voltage_switch)


  def test(self):
    if self.ready:
      self.releaseAll()
      time.sleep(1)
      self.pressAll()
      time.sleep(1)
      self.liftAll()
      time.sleep(1)


#############################################################################
class CardView(QWidget):
  def __init__(self, project):
    super().__init__()
    self.project = project

    self.cards = self.project.readCards()
    self.stamps = self.project.readStamps()

    self.grabKeyboard()

    self.font = QFont()
    self.font.setPixelSize(30)

    self.hardware = Hardware(self.switchEvent)

    self.selectCard(0)

  def closeEvent(self, event: QCloseEvent):
    self.hardware.close()

  def switchEvent(self):
    self.setColumn(self.column + 1)

  def selectCard(self, idx):
    self.idx = idx % len(self.cards)
    self.card = self.cards[self.idx]

    self.stamp = None
    for stamp in self.stamps:
      if stamp["name"] == self.card["name"]:
        self.stamp = stamp
        break

    self.setWindowTitle("Karten stanzen - " + self.card["name"])

    self.setColumn(0)

  def setColumn(self, column):
    if column >= 0 and column <= 60:
      self.column = column
      self.update()

      for i in range(16):
        if self.card["data"][self.column][i] == 1:
          self.hardware.press(i)
        else:
          self.hardware.release(i)

  def keyReleaseEvent(self, event: QKeyEvent):
    key = event.key()

    if key == Qt.Key.Key_Backspace:
      self.setColumn(0)
 
    if key == Qt.Key.Key_Space:
      self.setColumn(self.column + 1)
  
    if key == Qt.Key.Key_Up:
      self.selectCard(self.idx+1)

    if key == Qt.Key.Key_Down:
      self.selectCard(self.idx-1)
 
    if key == Qt.Key.Key_PageUp:
      self.selectCard(self.idx+10)

    if key == Qt.Key.Key_PageDown:
      self.selectCard(self.idx-10)
 
    if key == Qt.Key.Key_Right:
      self.selectCard(self.idx+int(len(self.cards)/2))

    if key == Qt.Key.Key_Left:
      self.selectCard(self.idx-int(len(self.cards)/2))

  def mouseReleaseEvent(self, event):
    x0 = int(self.width()/2)-630

    idx = math.floor((event.position().x()-20-x0)/20)
    self.setColumn(idx)

  def scanStamp(self):
    scanStamp(self.project.path, self.card["name"])

    self.stamps = self.project.readStamps()

    self.stamp = None
    for stamp in self.stamps:
      if stamp["name"] == self.card["name"]:
        self.stamp = stamp
        break

    self.update()

 
  def removeStamp(self):
    self.stamps = []
    for stamp in self.project.readStamps():
      if stamp["name"] != self.card["name"]:
        self.stamps.append(stamp)
    self.project.writeStamps(self.stamps)
    self.stamp = None
    self.update()
 
  def paintEvent(self, event: QPaintEvent):
    nobrush = Qt.BrushStyle.NoBrush
    blackbrush = QBrush("black")
    greenpen2 = QPen(QColor("green"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    redpen2 = QPen(QColor("red"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    nopen = QPen(Qt.PenStyle.NoPen)

    painter = QPainter(self)
    painter.setFont(self.font)

    x0 = int(self.width()/2)-630
    y0 = int(self.height()/2)-370

    if self.card:

      painter.fillRect(x0,y0,1260,340,QColor("gray"))
      painter.setBrush(QColor("black"))

      # set binding holes
      for x in [50,50+580,50+580+580]:
        for y in [50, 110, 230, 290]:
          painter.drawEllipse(QPoint(x0+x, y0+y), 7, 7)

      # set fixing holes
      for x in [50+30,50+580-30,50+580+30,50+580+580-30]:
        painter.drawEllipse(QPoint(x0+x, y0+170), 15, 15)

      # set data holes
      for c in range(60):
        for r in range(16):
          if self.card["data"][c][r] == 1:
            painter.drawEllipse(QPoint(x0+30+20*c, y0+20+20*r), 7, 7)

      # draw card number
      painter.drawText(x0+600,y0-20,self.card["name"])

      # draw selection
      painter.setPen(Qt.PenStyle.NoPen)
      painter.setBrush(QColor(255,0,0,100))
      painter.drawRect(x0+20+20*self.column, y0+0, 21, 340)

    else:
      painter.setPen("black")
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRect(x0,y0,1260,340)

    x0 = int(self.width()/2)-630
    y0 = int(self.height()/2)+30

    if self.stamp:
      painter.fillRect(x0,y0,1260,340,QColor("gray"))
      painter.setBrush(QColor("black"))

      # set binding holes
      for x in [50,50+580,50+580+580]:
        for y in [50, 110, 230, 290]:
          painter.drawEllipse(QPoint(x0+x, y0+y), 7, 7)

      # set fixing holes
      for x in [50+30,50+580-30,50+580+30,50+580+580-30]:
        painter.drawEllipse(QPoint(x0+x, y0+170), 15, 15)

      # set data holes
      for c in range(60):
        for r in range(16):
          if self.stamp["data"][c][r] == 1:
            painter.setBrush(blackbrush)
          else:
            painter.setBrush(nobrush)

          if self.stamp["data"][c][r] != self.card["data"][c][r]:
            painter.setPen(redpen2)
          else:
            painter.setPen(greenpen2)

          painter.drawEllipse(QPoint(x0+30+20*c, y0+20+20*r), 7, 7)

    else:
      painter.setPen("black")
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRect(x0,y0,1260,340)

    painter.end()

#############################################################################
class CardStamper(QMainWindow):
  def __init__(self, project):
    super().__init__()
    self.project = project

    self.setWindowTitle("JacqSuite")
    self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'assets', 'JacqSuite.ico')))

    test_action = QAction(QIcon('./src/assets/test.png'), 'Hardware testen', self)
    test_action.triggered.connect(self.test)

    reset_action = QAction(QIcon('./src/assets/reset.png'), 'Hardware zurücksetzen', self)
    reset_action.triggered.connect(self.reset)

    servo_action = QAction(QIcon('./src/assets/servo.png'), 'Servos kalibrieren', self)
    servo_action.triggered.connect(self.calibrate)

    poti_action = QAction(QIcon('./src/assets/poti.png'), 'Poti kalibrieren', self)
    poti_action.triggered.connect(self.calibratePoti)

    scan_action = QAction(QIcon('./src/assets/webcam.png'), 'Karte scannen', self)
    scan_action.triggered.connect(self.scan)

    remove_action = QAction(QIcon('./src/assets/remove-card.png'), 'Karte verwerfen', self)
    remove_action.triggered.connect(self.remove)

    close_action = QAction(QIcon('./src/assets/close.png'), 'Stanzen beenden', self)
    close_action.triggered.connect(self.close)

    self.setWindowTitle("Karten stanzen")
    self.resize(1300,1000)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    toolbar = QToolBar('Main ToolBar')
    toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    toolbar.setIconSize(QSize(64, 64))
    self.addToolBar(toolbar)

    toolbar.addAction(test_action)
    toolbar.addAction(servo_action)
    toolbar.addAction(poti_action)
    toolbar.addAction(reset_action)
    toolbar.addSeparator()
    toolbar.addAction(scan_action)
    toolbar.addAction(remove_action)
    toolbar.addWidget(spacer)
    toolbar.addAction(close_action)

    self.view = CardView(self.project)
    self.setCentralWidget(self.view)

  def showMessage(self, title, text):
    msgBox = QMessageBox(self)
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec()

  def closeEvent(self, event: QCloseEvent):
    self.view.close()

  def calibrate(self):
    self.view.hardware.calibrate()
    self.view.setColumn(0)
    self.showMessage("Servos kalibrieren", "Die Kalibrierung der Servomotoren ist abgeschlossen.")

  def calibratePoti(self):
    self.view.hardware.calibratePoti()
    self.view.setColumn(0)
    self.showMessage("Poti kalibrieren", "Die Kalibrierung des Potentiometers ist abgeschlossen.")

  def reset(self):
    self.view.hardware.reset()
    self.view.setColumn(0)
    self.showMessage("Hardware zurücksetzen", "Die Hardware wurde auf Standardeinstellungen zurückgesetzt.")

  def test(self):
    self.view.hardware.test()
    self.view.setColumn(0)
    self.showMessage("Hardware testen", "Der Test der Hardware ist abgeschlossen.")

  def scan(self):
    self.view.scanStamp()

  def remove(self):
    self.view.removeStamp()
