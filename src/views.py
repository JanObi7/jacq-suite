import cv2 as cv
import numpy as np
import math

from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QBrush, QKeyEvent, QPixmap, QWheelEvent, QImage, QColor, QPen
from PySide6.QtCore import Qt, Signal, Slot

z = 4

class PatternScene(QGraphicsScene):
    selectionChanged = Signal(int, int)

    def __init__(self, parent, fabric):
        super().__init__(parent)

        self.scanMode = True

        self.nk = fabric.config["pattern"]["nk"]
        self.ns = fabric.config["pattern"]["ns"]
        self.dk = fabric.config["pattern"]["dk"]
        self.ds = fabric.config["pattern"]["ds"]

        # scans
        filename = fabric.config["scans"][0]["filename"]
        limit = fabric.config["scans"][0]["limit"]
        kmin = fabric.config["scans"][0]["kmin"]
        kmax = fabric.config["scans"][0]["kmax"]
        smin = fabric.config["scans"][0]["smin"]
        smax = fabric.config["scans"][0]["smax"]
        point_tl = fabric.config["scans"][0]["point_tl"]
        point_tr = fabric.config["scans"][0]["point_tr"]
        point_bl = fabric.config["scans"][0]["point_bl"]
        point_br = fabric.config["scans"][0]["point_br"]

        scan = cv.imread(fabric.path+"/scans/"+filename, flags=cv.IMREAD_UNCHANGED)
        scan = cv.cvtColor(scan, cv.COLOR_BGR2RGB)
        scan_points = [point_tl, point_tr, point_bl, point_br]

        part_points = [[0,0], [z*self.ds*(kmax-kmin+1),0], [0,z*self.dk*(smax-smin+1)], [z*self.ds*(kmax-kmin+1),z*self.dk*(smax-smin+1)]]

        matrix = cv.getPerspectiveTransform(np.float32(scan_points), np.float32(part_points))
        self.scan = cv.warpPerspective(scan, matrix, (z*self.ds*self.nk, z*self.dk*self.ns))
        qimg = QImage(self.scan.data,self.scan.shape[1], self.scan.shape[0], QImage.Format.Format_RGB888)
        item = self.addPixmap(QPixmap(qimg))
        # # item.setPos(0, 4*z*self.dk)

        fabric.loadPattern()
        self.pattern = fabric.pattern
        img = self.getFramedPattern()
        print(img.shape)
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

        rx = 8
        ry = 0
        rw = 44
        rh = 12
        self.rapport = self.addRect(z*self.ds*rx, z*self.dk*(self.ns-ry-rh), z*self.ds*rw, z*self.dk*rh, QPen(QColor("yellow"), 1))

        self.selection = self.addRect(0,0,z*self.ds*self.dk,z*self.ds*self.dk, QPen(QColor("cyan"),z))
        self.selection.setVisible(False)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if not event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.k1 = math.floor(event.scenePos().x() / z / self.ds)
            self.s1 = math.floor(event.scenePos().y() / z / self.dk)

        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if not event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.k2 = math.floor(event.scenePos().x() / z / self.ds)
            self.s2 = math.floor(event.scenePos().y() / z / self.dk)
            self.updateSelection()

        return super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            k = math.floor(event.scenePos().x() / z / self.ds)
            s = math.floor(event.scenePos().y() / z / self.dk)

            if k >= 0 and k < self.nk and s >= 0 and s < self.ns:
                if tuple(self.pattern[s,k]) == (255,255,255,255):
                    self.pattern[s,k] = (255,0,0,255)
                else:
                    self.pattern[s,k] = (255,255,255,255)
                self.updatePattern()

        else:
            self.k2 = math.floor(event.scenePos().x() / z / self.ds)
            self.s2 = math.floor(event.scenePos().y() / z / self.dk)
            self.updateSelection()

        return super().mouseReleaseEvent(event)
    
    def updateSelection(self):
        self.selection.setRect(z*self.ds*self.k1, z*self.dk*self.s1, z*self.ds*(self.k2-self.k1+1), z*self.dk*(self.s2-self.s1+1))
        self.selection.setVisible(True)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        print(key)

        if key == Qt.Key.Key_Space:
            self.pattern[self.s1:self.s2+1,self.k1:self.k2+1] = self.detect(self.scan[z*self.dk*self.s1:z*self.dk*(self.s2+1), z*self.ds*self.k1:z*self.ds*(self.k2+1)], self.k2-self.k1+1, self.s2-self.s1+1, z*self.ds, z*self.dk, 160)
            self.updatePattern()

        if key == Qt.Key.Key_M:
            self.toggleMode()

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
        img = self.getFramedPattern()
        qimg = QImage(img.data,img.shape[1], img.shape[0], QImage.Format.Format_RGBA8888)
        self.pixmap.setPixmap(QPixmap(qimg))

    @Slot()
    def showRapport(self):
        self.rapport.setVisible(not self.rapport.isVisible())

    @Slot()
    def toggleMode(self):
        self.scanMode = not self.scanMode
        self.updatePattern()

    def getFramedPattern(self):
        if self.scanMode:
            img = np.zeros((z*self.dk*self.ns, z*self.ds*self.nk, 4), np.uint8)
            for s in range(self.ns):
                for k in range(self.nk):
                    color = (int(self.pattern[s,k][0]), int(self.pattern[s,k][1]), int(self.pattern[s,k][2]), int(self.pattern[s,k][3]))
                    cv.rectangle(img, (z*self.ds*k+1,z*self.dk*s+1), (z*self.ds*(k+1)-2,z*self.dk*(s+1)-2), color, 2)
        else:
            img = cv.resize(self.pattern, (z*self.ds*self.nk, z*self.dk*self.ns), interpolation=cv.INTER_NEAREST)
        
        return img #cv.cvtColor(img, cv.COLOR_BGRA2RGBA)


class PatternView(QGraphicsView):
    def __init__(self, parent, fabric):
        super().__init__(parent)

        self.setBackgroundBrush(QBrush("#DFD5C2"))

        self.scene = PatternScene(self, fabric)

        self.setScene(self.scene)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            dy = event.angleDelta().y()
            if dy > 0:
                self.scale(1.25,1.25)
            else:
                self.scale(0.8,0.8)

        return super().wheelEvent(event)
