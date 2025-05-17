from PySide6 import QtWidgets
from PySide6.QtCore import QSize, QPoint, Qt
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPainter, QColor, QBrush, QPen, QKeyEvent
from PySide6.QtWidgets import QWidget
import JacqCard

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_io4_v2 import BrickletIO4V2
from tinkerforge.bricklet_analog_in_v3 import BrickletAnalogInV3

import time, math

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
      # init tinkerforge
      self.ipcon = IPConnection() # Create IP connection
      self.ipcon.set_timeout(0.1)
      self.s1 = BrickletServoV2(self.UID_S1, self.ipcon) # Create device object
      self.s2 = BrickletServoV2(self.UID_S2, self.ipcon) # Create device object
      # self.io = BrickletIO4V2(self.UID_IO, self.ipcon) # Create device object
      self.ai = BrickletAnalogInV3(self.UID_AI, self.ipcon) # Create device object
      self.ipcon.connect(self.HOST, self.PORT) # Connect to brickd

      pmin = 80
      self.mapping = [
        (self.s1, 9, pmin, 180),
        (self.s1, 8, pmin, 180),
        (self.s1, 7, pmin, 180),
        (self.s1, 6, pmin, 180),
        (self.s1, 3, pmin, 180),
        (self.s1, 2, pmin, 180),
        (self.s1, 1, pmin, 180),
        (self.s1, 0, pmin, 180),
        (self.s2, 9, pmin, 180),
        (self.s2, 8, pmin, 180),
        (self.s2, 7, pmin, 180),
        (self.s2, 6, pmin, 180),
        (self.s2, 3, pmin, 180),
        (self.s2, 2, pmin, 180),
        (self.s2, 1, pmin, 180),
        (self.s2, 0, pmin, 180),
      ]
      # configure and enable servos
      for i in range(16):
        s, p, dmin, dmax = self.mapping[i]
        s.set_pulse_width(p, 500, 2500)
        s.set_degree(p, 0, 180)
        s.set_motion_configuration(p, 500000, 500000, 500000)
        s.set_enable(p, True)    

      # configure io
      # self.io.register_callback(self.io.CALLBACK_INPUT_VALUE, callback)
      # self.io.set_input_value_callback_configuration(0, 50, True)

      # configure ao
      self.ai.register_callback(self.ai.CALLBACK_VOLTAGE, callback)
      self.ai.set_voltage_callback_configuration(10, True, 'x', 0, 5)

      self.pressAll()
      self.releaseAll()

      print("hardware initialized")

    except Exception as e:
      print(e)
      print("hardware not initialized")

  def __del__(self):
    self.releaseAll()

    # disable servos
    try:
      for i in range(16):
        s, p, dmin, dmax = self.mapping[i]
        s.set_enable(p, False)
    except:
      pass

    # deinit tinkerforge
    try:
      self.ipcon.disconnect()
      print("hardware deinitialized")
    except:
      print("hardware not deinitialized")

  def releaseAll(self):
    # release all
    for i in range(16):
      self.release(i)

    # wait for releasing
    time.sleep(2)

  def pressAll(self):
    # release all
    for i in range(16):
      self.press(i)

    # wait for releasing
    time.sleep(2)

  def release(self, i):
    try:
      s, p, dmin, dmax = self.mapping[i]
      s.set_position(p, dmax)
    except:
      pass

  def press(self, i):
    try:
      s, p, dmin, dmax = self.mapping[i]
      s.set_position(p, dmin)
    except:
      pass


#############################################################################
class CardStamper(QWidget):
  def __init__(self, cards):
    super().__init__()

    self.setWindowTitle("Karten stanzen")

    self.last_voltage = 5000
    self.switch_voltage = 1100
    self.max_voltage = 1250
    self.min_voltage = 250
    self.hardware = Hardware(self.hardwareAiEvent)

    self.cards = cards
    self.selectCard(0)

  def closeEvent(self, event: QCloseEvent):
    del self.hardware

  def selectCard(self, idx):
    self.idx = idx
    self.card = self.cards[idx]

    self.setWindowTitle("Karten stanzen - " + self.card["name"])

    self.setColumn(-1)

  def sizeHint(self):
    return QSize(1260,340)
  
  def setColumn(self, column):
    if (column >= -2 and column <= 58):
      self.column = column
      self.repaint()
    
      if column >= 0 and column <= 27:
        c = self.column+1
      elif column >= 29 and column <= 56:
        c = self.column  
      else:
        c = -1

      for i in range(16):
        dot = f"dot_{c}_{i+1}"
        if dot in self.card and self.card[dot] == "1":
          self.hardware.press(i)
        else:
          self.hardware.release(i)

  def hardwareIoEvent(self, channel, changed, value):
    print("switch pressed")
    if channel == 0 and changed and value == False:
      self.setColumn(self.column + 1)

  def hardwareAiEvent(self, voltage):
    if self.last_voltage < self.switch_voltage and voltage >= self.switch_voltage:
      print("switch", voltage)
      self.setColumn(self.column + 1)

    self.last_voltage = voltage

  def keyReleaseEvent(self, event: QKeyEvent):
    key = event.key()

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
    idx = math.floor((event.position().x()-50-10)/20)
    self.setColumn(idx)
 
  def paintEvent(self, event: QPaintEvent):
    painter = QPainter(self)
    painter.fillRect(0,0,1260,340,QColor("gray"))

    painter.setBrush(QColor("black"))

    # set binding holes
    for x in [50,50+580,50+580+580]:
      for y in [50, 110, 230, 290]:
        painter.drawEllipse(QPoint(x, y), 7, 7)

    # set fixing holes
    for x in [50+30,50+580-30,50+580+30,50+580+580-30]:
      painter.drawEllipse(QPoint(x, 170), 15, 15)

    # set data holes
    for c in range(28):
      for r in range(16):
        # block 1
        dot = f'dot_{c+1}_{r+1}'
        if dot in self.card:
          if self.card[dot] == "1":
            painter.drawEllipse(QPoint(50+20+20*c, 20+20*r), 7, 7)

        # block 2
        dot = f'dot_{28+c+1}_{r+1}'
        if dot in self.card:
          if self.card[dot] == "1":
            painter.drawEllipse(QPoint(50+580+20+20*c, 20+20*r), 7, 7)

    # draw selection
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255,0,0,100))
    painter.drawRect(50+10+20*self.column, 0, 21, 340)




if __name__ == '__main__':
  import JacqCard
  cards = JacqCard.readCards("D:/temp/jacq-suite/data/D689_P524")

  app = QtWidgets.QApplication()
  win = CardStamper(cards)
  win.show()
  app.exec()
