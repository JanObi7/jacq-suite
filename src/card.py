from PySide6 import QtWidgets
from PySide6.QtCore import QSize, QPoint, Qt
from PySide6.QtGui import QCloseEvent, QPaintEvent, QPainter, QColor, QBrush, QPen, QKeyEvent
from PySide6.QtWidgets import QWidget
import JacqCard

from tinkerforge.ip_connection import IPConnection
from tinkerforge.brick_servo import BrickServo
import time, math

#############################################################################
class Actuators:
  HOST = "localhost"
  PORT = 4223
  UID = "6JKyxU"

  n = 4

  def __init__(self):
    try:
      # init tinkerforge
      self.ipcon = IPConnection() # Create IP connection
      self.ipcon.set_timeout(0.1)
      self.srv = BrickServo(self.UID, self.ipcon) # Create device object
      self.ipcon.connect(self.HOST, self.PORT) # Connect to brickd

      # configure and enable servos
      for i in range(self.n):
        self.srv.set_pulse_width(i, 500, 2500)
        self.srv.set_degree(i, 0, 180)
        self.srv.set_acceleration(i, 65535)
        self.srv.set_velocity(i, 65535)
        self.srv.enable(i)    

        self.release(i)

      # wait for releasing
      time.sleep(2)

      print("hardware initialized")

    except:
      print("hardware not initialized")

  def __del__(self):
    try:
      for i in range(self.n):
        self.release(i)
    except:
      pass

    # wait for releasing
    time.sleep(2)

    # disable servos
    try:
      for i in range(self.n):
        self.srv.disable(i)
    except:
      pass

    # deinit tinkerforge
    try:
      self.ipcon.disconnect()
      print("hardware deinitialized")
    except:
      print("hardware not deinitialized")

  def release(self, i):
    try:
      self.srv.set_position(i, 180)
    except:
      pass

  def press(self, i):
    try:
      self.srv.set_position(i, 90)
    except:
      pass


#############################################################################
class CardStamper(QWidget):
  def __init__(self, cards):
    super().__init__()

    self.setWindowTitle("Karten stanzen")

    self.hardware = Actuators()

    self.cards = cards
    self.selectCard(0)

  def closeEvent(self, event: QCloseEvent):
    del self.hardware

  def selectCard(self, idx):
    self.idx = idx
    self.card = self.cards[idx]

    self.setWindowTitle("Karten stanzen - " + self.card["name"])

    self.setColumn(0)

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

      for i in  range(4):
        dot = f"dot_{c}_{i+1}"
        if dot in self.card and self.card[dot] == "1":
          self.hardware.press(i)
        else:
          self.hardware.release(i)

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
  cards = JacqCard.readCards("C:/temp/jacq-suite/data/P524_W.218.9")

  app = QtWidgets.QApplication()
  win = CardStamper(cards)
  win.show()
  app.exec()
