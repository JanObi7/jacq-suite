import cv2 as cv
import numpy as np

class Digitizer:
  def run(self, pattern, scan, points, kmin, kmax, smin, smax, dk, ds, limit):
    self.bs = 0
    self.bk = 0

    self.os = 0
    self.ok = 0

    self.target = None
    self.box_pattern = None
    self.m = 50

    self.shift = False

    self.pattern = pattern
    self.scan = scan
    self.dk = dk
    self.ds = ds
    self.r = round(dk/ds)

    # Umrechnung in Bildkoordinaten
    ps, pk = np.shape(pattern)
    self.kmin = kmin - 1
    self.kmax = kmax
    self.smin = ps - smax
    self.smax = ps - smin + 1

    # set local aparameter
    self.z = 2

    self.nk = self.kmax - self.kmin
    self.ns = self.smax - self.smin

    part_points = [
      [0, 0], [self.z*self.nk, 0],
      [0, self.z*self.r*self.ns], [self.z*self.nk, self.z*self.r*self.ns]
    ]

    self.matrix = cv.getPerspectiveTransform(np.float32(points), np.float32(part_points))

    self.part = cv.warpPerspective(self.scan, self.matrix, (self.z*self.nk, self.z*self.r*self.ns))

    cv.namedWindow('part')
    cv.setMouseCallback('part', self.map_event)
    cv.namedWindow('box')
    cv.setMouseCallback('box', self.box_event)

    self.box_pattern = self.pattern[self.smin+self.ds*self.bs:self.smin+self.ds*self.bs+self.ds,self.kmin+self.dk*self.bk:self.kmin+self.dk*self.bk+self.dk]
    self.showPart()
    self.showBox()

    while True:
      k = cv.waitKey(20) & 0xFF

      if k == 56:
        self.os += 1
        self.showBox()
      if k == 50:
        self.os -= 1
        self.showBox()
      if k == 52:
        self.ok += 1
        self.showBox()
      if k == 54:
        self.ok -= 1
        self.showBox()

      # detect
      if k == 32:
        self.box_pattern = detect(self.target, self.dk, self.ds, 10*self.ds, 10*self.dk, limit)
        self.showBox()

        # save direct to pattern
        self.saveBoxToPattern()

      # copy
      if k == ord("c"):
        self.box_copy = self.box_pattern.copy()

      # paste
      if k == ord("v"):
        self.box_pattern  = self.box_copy
        
        self.saveBoxToPattern()
        self.showBox()

      # # save
      # if k == 13:
      #   self.pattern[self.smin+self.ds*self.bs:self.smin+self.ds*self.bs+self.ds,self.kmin+self.dk*self.bk:self.kmin+self.dk*self.bk+self.dk] = self.box_pattern
      #   self.showPart()

      if k == 27 or cv.getWindowProperty("part", cv.WND_PROP_VISIBLE) < 1 or cv.getWindowProperty("box", cv.WND_PROP_VISIBLE) < 1:
        # save direct to pattern
        self.saveBoxToPattern()
        break

    cv.destroyAllWindows()

    return self.pattern
  
  def saveBoxToPattern(self):
    self.pattern[self.smin+self.ds*self.bs:self.smin+self.ds*self.bs+self.ds,self.kmin+self.dk*self.bk:self.kmin+self.dk*self.bk+self.dk] = self.box_pattern
    self.showPart()

  def showBox(self):
    invmat = np.linalg.inv(self.matrix)

    x1, y1, f1 = np.matmul(invmat, np.float32([self.z*self.dk*self.bk,self.z*self.r*self.ds*self.bs,1]))
    x2, y2, f2 = np.matmul(invmat, np.float32([self.z*self.dk*self.bk+self.z*self.dk,self.z*self.r*self.ds*self.bs,1]))
    x3, y3, f3 = np.matmul(invmat, np.float32([self.z*self.dk*self.bk,self.z*self.r*self.ds*self.bs+self.z*self.r*self.ds,1]))
    x4, y4, f4 = np.matmul(invmat, np.float32([self.z*self.dk*self.bk+self.z*self.dk,self.z*self.r*self.ds*self.bs+self.z*self.r*self.ds,1]))

    scan_points = [
      [x1/f1, y1/f1], [x2/f2, y2/f2],
      [x3/f3, y3/f3], [x4/f4, y4/f4],
    ]

    size = 10*self.dk*self.ds

    box_points = [
      [self.m+0+self.ok, self.m+0+self.os], [self.m+size+self.ok, self.m+0+self.os],
      [self.m+0+self.ok, self.m+size+self.os], [self.m+size+self.ok, self.m+size+self.os],
    ]

    box_matrix = cv.getPerspectiveTransform(np.float32(scan_points), np.float32(box_points))

    box = cv.warpPerspective(self.scan, box_matrix, (2*self.m+size, 2*self.m+size))

    self.target = box[self.m:self.m+size,self.m:self.m+size]

    for k in range(self.dk+1):
      cv.line(box, (self.m+10*self.ds*k, self.m+0), (self.m+10*self.ds*k, self.m+10*self.dk*self.ds), (255,255,255), 1)
    for s in range(self.ds+1):
      cv.line(box, (self.m+0, self.m+10*self.dk*s), (self.m+10*self.dk*self.ds, self.m+10*self.dk*s), (255,255,255), 1)

    if self.box_pattern is not None:
      for s in range(self.ds):
        for k in range(self.dk):
          if self.box_pattern[s,k] == 255:
            color = (255,255,255)
          elif self.box_pattern[s,k] == 0:
            color = (0,0,255)
          else:
            color = (255,0,0)

          cv.rectangle(box, (self.m+10*self.ds*k+2, self.m+10*self.dk*s+2), (self.m+10*self.ds*k+10*self.ds-2, self.m+10*self.dk*s+10*self.dk-2), color, 4) 

    cv.imshow("box", box)

  def showPart(self):
    map = self.part.copy()

    for k in range(self.nk):
      for s in range(self.ns):
        if self.pattern[self.smin+s,self.kmin+k] == 255: color = (255,255,255)
        elif self.pattern[self.smin+s,self.kmin+k] == 0: color = (0,0,0)
        else: color = (255,0,0)
        
        map[self.z*self.r*s+self.z*1,self.z*k] = color

    for k in range(self.dk,self.nk,self.dk):
      cv.line(map, (self.z*k, 0), (self.z*k, self.z*self.r*self.ns), (255,255,255), 1)
    for s in range(self.ds,self.ns,self.ds):
      cv.line(map, (0, self.z*self.r*s), (self.z*self.nk, self.z*self.r*s), (255,255,255), 1)

    cv.rectangle(map, (self.z*self.dk*self.bk,self.z*self.ds*self.r*self.bs), (self.z*self.dk*self.bk+self.z*self.dk,self.z*self.ds*self.r*self.bs+self.z*self.ds*self.r), (255,255,0), 3)

    cv.imshow("part", map)

  def map_event(self, event,x,y,flags,param):
    if event == cv.EVENT_LBUTTONUP:
      self.bs = int(y / self.ds / self.r / self.z)
      self.bk = int(x / self.dk / self.z)

      self.box_pattern = self.pattern[self.smin+self.ds*self.bs:self.smin+self.ds*self.bs+self.ds,self.kmin+self.dk*self.bk:self.kmin+self.dk*self.bk+self.dk]
      self.showPart()
      self.showBox()

  def box_event(self, event,x,y,flags,param):
    if event == cv.EVENT_LBUTTONUP:
      ix = int((x-self.m) / 10 / self.ds)
      iy = int((y-self.m) / 10 / self.dk)
      
      if self.box_pattern[iy,ix] == 0: self.box_pattern[iy,ix] = 255
      elif self.box_pattern[iy,ix] == 255: self.box_pattern[iy,ix] = 0
      else: self.box_pattern[iy,ix] = 255

      self.showBox()

      # save direct to pattern
      self.saveBoxToPattern()

    if event == cv.EVENT_RBUTTONDOWN:
      if not self.shift:
        self.shift = True
        self.shiftx = x
        self.shifty = y

    if event == cv.EVENT_RBUTTONUP:
      if self.shift:
        self.shift = False
        self.shiftx = 0
        self.shifty = 0

    if event == cv.EVENT_MOUSEMOVE:
      if self.shift:
        self.ok += x - self.shiftx
        self.os += y - self.shifty
        self.shiftx = x
        self.shifty = y

        self.showBox()

###################################################################
def detect(src, nx, ny, fx, fy, limit):
  mask = cv.cvtColor(src, cv.COLOR_BGR2HLS)
  mask = cv.inRange(mask[:,:,1], limit, 255)
  # cv.imshow("mask1", mask)

  target = np.zeros((ny,nx), np.uint8)

  for x in range(nx):
    for y in range(ny):
      sub = mask[fy*y+1:fy*y+fy-1,fx*x+1:fx*x+fx-1]
      sum = np.sum(sub)
      smax = 255*(fx-2)*(fy-2)
      
      if sum > 0.4*smax:
        color = 255
      elif sum < 0.2*smax:
        color = 0
      else:
        color = 127

      target[y,x] = color

  return target
 
###################################################################
def selectScanPoint(pathname):
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