import cv2 as cv
import numpy as np
import math

from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QListView, QMainWindow
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QBrush, QKeyEvent, QPixmap, QWheelEvent, QImage, QColor, QPen, QIcon
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal, Slot

from project import Project

z = 2

class PatternScene(QGraphicsScene):
    selectionChanged = Signal(int, int)

    def __init__(self, parent, project):
        super().__init__(parent)

        self.scanMode = True
        self.tileMode = True
        self.project = project

        self.nk = self.project.config["design"]["width"]
        self.ns = self.project.config["design"]["height"]
        self.dk = self.project.config["design"]["dx"]
        self.ds = self.project.config["design"]["dy"]

        layer = self.project.scans
        qimg = QImage(layer.data,layer.shape[1], layer.shape[0], QImage.Format.Format_RGB888)
        self.scans = self.addPixmap(QPixmap(qimg))
        self.ox = 0
        self.oy = 0

        img = self.project.getDesign(self.scanMode, 1, 1, 1, 1)
        qimg = QImage(img.data,img.shape[1], img.shape[0], QImage.Format.Format_RGBA8888)
        self.pixmap = self.addPixmap(QPixmap(qimg))

        for k in range(0,self.nk+1):
            self.addLine(z*self.ds*k,0,z*self.ds*k,z*self.dk*self.ns,QPen(QColor("gray"),z*0.5))
        for s in range(0,self.ns+1):
            self.addLine(0,z*self.dk*s,z*self.ds*self.nk,z*self.dk*s,QPen(QColor("gray"),z*0.5))
        for k in range(0,self.nk+self.dk,self.dk):
            self.addLine(z*self.ds*k,0,z*self.ds*k,z*self.dk*self.ns,QPen(QColor("black"),z*0.5))
        for s in range(0,self.ns+self.ds,self.ds):
            self.addLine(0,z*self.dk*s,z*self.ds*self.nk,z*self.dk*s,QPen(QColor("black"),z*0.5))

        # rx = 8
        # ry = 0
        # rw = 44
        # rh = 12
        # self.rapport = self.addRect(z*self.ds*rx, z*self.dk*(self.ns-ry-rh), z*self.ds*rw, z*self.dk*rh, QPen(QColor("yellow"), 1))

        self.selection = self.addRect(0,0,z*self.ds*self.dk,z*self.ds*self.dk, QPen(QColor("cyan"), 4*z))
        self.selection.setVisible(False)

        self.k1 = 1
        self.k2 = 1
        self.s1 = 1
        self.s2 = 1
        self.selecting = False

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if not event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.selecting = True
            self.k1 = math.floor(event.scenePos().x() / z / self.ds)
            self.s1 = math.floor(event.scenePos().y() / z / self.dk)
            self.k2 = self.k1
            self.s2 = self.s1

            if self.tileMode:
                self.k1 = math.floor(self.k1/self.dk)*self.dk
                self.s1 = math.floor(self.s1/self.ds)*self.ds
                self.k2 = math.floor(self.k2/self.dk+1)*self.dk-1
                self.s2 = math.floor(self.s2/self.ds+1)*self.ds-1

            self.updateSelection()


        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if not event.modifiers() == Qt.KeyboardModifier.ControlModifier and self.selecting:
            self.k2 = math.floor(event.scenePos().x() / z / self.ds)
            self.s2 = math.floor(event.scenePos().y() / z / self.dk)

            if self.tileMode:
                self.k2 = math.floor(self.k2/self.dk+1)*self.dk-1
                self.s2 = math.floor(self.s2/self.ds+1)*self.ds-1

            self.updateSelection()

        return super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            k = math.floor(event.scenePos().x() / z / self.ds)
            s = math.floor(event.scenePos().y() / z / self.dk)

            if k >= 0 and k < self.nk and s >= 0 and s < self.ns:
                if tuple(self.project.design[s,k]) == (255,255,255,255):
                    self.project.design[s,k] = (255,0,0,255)
                else:
                    self.project.design[s,k] = (255,255,255,255)
                self.updatePattern()

        elif self.selecting:
            self.selecting = False
            self.k2 = math.floor(event.scenePos().x() / z / self.ds)
            self.s2 = math.floor(event.scenePos().y() / z / self.dk)

            if self.tileMode:
                self.k2 = math.floor(self.k2/self.dk+1)*self.dk-1
                self.s2 = math.floor(self.s2/self.ds+1)*self.ds-1

            self.updateSelection()

        return super().mouseReleaseEvent(event)
    
    def updateSelection(self):
        self.selection.setRect(z*self.ds*self.k1, z*self.dk*self.s1, z*self.ds*(self.k2-self.k1+1), z*self.dk*(self.s2-self.s1+1))
        self.selection.setVisible(True)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        # print(key)

        if key == Qt.Key.Key_Space:
            self.project.design[self.s1:self.s2+1,self.k1:self.k2+1] = self.detect(self.project.scans[z*self.dk*self.s1-self.oy:z*self.dk*(self.s2+1)-self.oy, z*self.ds*self.k1-self.ox:z*self.ds*(self.k2+1)-self.ox], self.k2-self.k1+1, self.s2-self.s1+1, z*self.ds, z*self.dk, 180)
            self.updatePattern()

        if key == Qt.Key.Key_1:
            self.project.design[self.s1:self.s2+1,self.k1:self.k2+1] = (255,0,0,255)
            self.updatePattern()

        if key == Qt.Key.Key_0:
            self.project.design[self.s1:self.s2+1,self.k1:self.k2+1] = (255,255,255,255)
            self.updatePattern()

        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.project.design[self.s1:self.s2+1,self.k1:self.k2+1] = (0,0,0,0)
            self.updatePattern()

        if key == Qt.Key.Key_M:
            self.toggleMode()

        if key == Qt.Key.Key_B:
            self.tileMode = not self.tileMode

        if key == Qt.Key.Key_C:
            self.buffer = self.project.design[self.s1:self.s2+1, self.k1:self.k2+1]

        if key == Qt.Key.Key_V:
            cy, cx, _ = self.buffer.shape
            px = self.k2-self.k1+1
            py = self.s2-self.s1+1

            if px % cx == 0 and py % cy == 0:
                for j in range(int(py/cy)):
                    for i in range(int(px/cx)):
                        self.project.design[self.s1+j*cy:self.s1+(j+1)*cy, self.k1+i*cx:self.k1+(i+1)*cx] = self.buffer

            self.updatePattern()

        if key == Qt.Key.Key_A:
            self.ox -= 1
            self.scans.setPos(self.ox, self.oy)

        if key == Qt.Key.Key_D:
            self.ox += 1
            self.scans.setPos(self.ox, self.oy)

        if key == Qt.Key.Key_W:
            self.oy -= 1
            self.scans.setPos(self.ox, self.oy)

        if key == Qt.Key.Key_S:
            self.oy += 1
            self.scans.setPos(self.ox, self.oy)

        if key == Qt.Key.Key_R:
            self.project.config["design"]["rx"] = self.k1
            self.project.config["design"]["ry"] = self.project.config["design"]["height"] - self.s2 - 1
            self.project.config["design"]["rw"] = self.k2-self.k1+1
            self.project.config["design"]["rh"] = self.s2-self.s1+1
            self.project.saveConfig()


        return super().keyReleaseEvent(event)

    def detect(self, src, nx, ny, fx, fy, limit):
      mask = cv.cvtColor(src, cv.COLOR_BGR2HLS)
      mask = cv.inRange(mask[:,:,1], limit, 255)
      # cv.imshow("debug", mask)

      target = np.zeros((ny,nx,4), np.uint8)

      for x in range(nx):
        for y in range(ny):
          sub = mask[fy*y+1:fy*y+fy-1,fx*x+1:fx*x+fx-1]
          sum = np.sum(sub)
          smax = 255*(fx-2)*(fy-2)
          
          if sum > 0.4*smax:
            color = (255,255,255,255)
          elif sum < 0.2*smax:
            color = (255,0,0,255)
          else:
            color = (0,0,255,255)

          target[y,x] = color

      return target

    @Slot()
    def updatePattern(self):
        img = self.project.getDesign(self.scanMode, self.k1, self.k2, self.s1, self.s2)
        qimg = QImage(img.data,img.shape[1], img.shape[0], QImage.Format.Format_RGBA8888)
        self.pixmap.setPixmap(QPixmap(qimg))

        self.project.saveDesign()

    def updateScans(self):
        img = self.project.scans
        qimg = QImage(img.data,img.shape[1], img.shape[0], QImage.Format.Format_RGB888)
        self.scans.setPixmap(QPixmap(qimg))

    @Slot()
    def showRapport(self):
        self.rapport.setVisible(not self.rapport.isVisible())

    @Slot()
    def toggleMode(self):
        self.scanMode = not self.scanMode
        self.updatePattern()

class PatternView(QGraphicsView):
    def __init__(self, parent, project):
        super().__init__(parent)

        self.setBackgroundBrush(QBrush("#DFD5C2"))

        self.scene = PatternScene(self, project)

        self.setScene(self.scene)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            dy = event.angleDelta().y()
            if dy > 0:
                self.scale(1.25,1.25)
            else:
                self.scale(0.8,0.8)

        return super().wheelEvent(event)

class PointSelectorScene(QGraphicsScene):
    def __init__(self, parent, filename):
        super().__init__(parent)

        scan = cv.imread(filename, flags=cv.IMREAD_UNCHANGED)
        scan = cv.cvtColor(scan, cv.COLOR_BGR2RGB)  
        qimg = QImage(scan.data,scan.shape[1], scan.shape[0], QImage.Format.Format_RGBA8888)
        # self.pixmap = self.addPixmap(QPixmap(qimg))
        self.addLine(0,0,100,100,QPen(QColor("black")))

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print(event)
        self.x = event.scenePos().x()
        self.y = event.scenePos().y()

        return super().mouseReleaseEvent(event)

class PointSelector(QGraphicsView):
    def __init__(self, parent, filename):
        super().__init__(parent)

        self.scene = PointSelectorScene(self, filename)

        self.setScene(self.scene)

    def wheelEvent(self, event: QWheelEvent) -> None:
        dy = event.angleDelta().y()
        if dy > 0:
            self.scale(1.25,1.25)
        else:
            self.scale(0.8,0.8)

        return super().wheelEvent(event)

