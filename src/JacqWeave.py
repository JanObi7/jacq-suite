import numpy as np
import cv2 as cv

def getColor1(x):
  schwarz = (50,50,50)
  grau1 = (100,100,100)
  grau2 = (120,120,120)
  gruen = (100,110,100)
  rot = (150,100,100)
  if x < 16: ck = grau1
  elif x < 18: ck = schwarz
  elif x < 30: ck = gruen
  elif x < 32: ck = schwarz
  elif x < 38: ck = grau2
  elif x < 40: ck = schwarz
  elif x < 48: ck = gruen
  elif x < 50: ck = schwarz
  elif x < 150: ck = rot
  elif x < 152: ck = schwarz
  elif x < 160: ck = gruen
  elif x < 162: ck = schwarz
  elif x < 168: ck = grau2
  elif x < 170: ck = schwarz
  elif x < 182: ck = gruen
  elif x < 184: ck = schwarz
  elif x < 216: ck = grau1
  elif x < 218: ck = schwarz
  elif x < 230: ck = gruen
  elif x < 232: ck = schwarz
  elif x < 240: ck = grau2
  elif x < 242: ck = schwarz
  elif x < 248: ck = gruen
  elif x < 250: ck = schwarz
  elif x < 350: ck = rot
  elif x < 352: ck = schwarz
  elif x < 360: ck = gruen
  elif x < 362: ck = schwarz
  elif x < 368: ck = grau2
  elif x < 370: ck = schwarz
  elif x < 382: ck = gruen
  elif x < 384: ck = schwarz
  elif x < 400: ck = grau1
  else: ck = rot

  return ck

def lighten(color, percent):
  return (
    int(color[0]/100*(100+percent)),
    int(color[1]/100*(100+percent)),
    int(color[2]/100*(100+percent)),
  )

################################################################################################
def render(pattern):
  ns, nk, _ = np.shape(program)

  nx = int(nk/3)
  ny = int(ns/3)

  # build image
  image_front = np.zeros((12*ny, 7*nx, 3), np.uint8)
  image_back = np.zeros((12*ny, 7*nx, 3), np.uint8)

  # getter and setter
  def get(k, s):
    return tuple(pattern[ns-1-s%ns, k%nk].tolist()) == (255, 0, 0, 255)


  # iterate over pattern
  for y in range(ny):
    for x in range(nx):
      def set_front(xmin, xmax, ymin, ymax, c):
        image_front[12*ny-1-12*y-ymax-1:12*ny-1-12*y-ymin, 7*x+xmin:7*x+xmax+1] = c

      def set_back(xmin, xmax, ymin, ymax, c):
        image_back[12*ny-1-12*y-ymax-1:12*ny-1-12*y-ymin, 7*nx-1-7*x-xmax-1:7*nx-1-7*x-xmin] = c

      cs1 = (20,20,20)
      cs2 = (200,200,200)
      cs3 = (20,20,20)

      ck1 = getColor1(x)
      ck2 = (200,200,200)
      ck3 = (20,20,20)

      b11 = get(3*x, 3*y)
      b21 = get(3*x+1, 3*y)
      b31 = get(3*x+2, 3*y)
      b12 = get(3*x, 3*y+1)
      b22 = get(3*x+1, 3*y+1)
      b32 = get(3*x+2, 3*y+1)
      b13 = get(3*x, 3*y+2)
      b23 = get(3*x+1, 3*y+2)
      b33 = get(3*x+2, 3*y+2)

      # Muster rot - S2 oben
      if b21 and b22:
        set_front(0, 6, 0, 8, lighten(cs2, -25))
        set_front(0, 6, 2, 7, lighten(cs2, 0))
        set_front(0, 6, 4, 6, lighten(cs2, +10))

        set_back(0, 6, 0, 8, lighten(cs1, 0))
        set_back(0, 6, 2, 7, lighten(cs1, 100))
        set_back(0, 6, 4, 6, lighten(cs1, 150))

      # Muster weiß - S1 oben
      if b11 and b12:
        set_front(0, 4, 0, 8, lighten(ck1, -25))
        set_front(1, 3, 2, 7, lighten(ck1, 0))
        set_front(2, 2, 4, 6, lighten(ck1, +10))

        set_front(5, 6, 0, 8, lighten(cs1, -25))
        set_front(5, 6, 2, 7, lighten(cs1, 0))
        set_front(5, 6, 4, 6, lighten(cs1, +10))

        set_back(0, 6, 0, 8, lighten(cs2, -25))
        set_back(0, 6, 2, 7, lighten(cs2, 0))
        set_back(0, 6, 4, 6, lighten(cs2, +10))

      # Kette 3
      if not b21 and not b22:
        set_back(5, 5, 0, 8, ck2)

      if not b31 and not b32:
        set_back(6, 6, 0, 8, ck3)

      # Bindschuss
      set_front(0, 5, 9, 11, lighten(cs3, 0))
      set_front(0, 5, 10, 10, lighten(cs3, 20))

      set_front(6, 6, 9, 11, lighten(ck3, 0))
      set_front(6, 6, 10, 10, lighten(ck3, 20))

      set_back(0, 4, 9, 11, lighten(ck1, -50))
      set_back(1, 3, 9, 11, lighten(ck1, -20))
      set_back(2, 2, 9, 11, lighten(ck1, 0))
      set_back(5, 5, 9, 11, ck2)
      set_back(6, 6, 9, 11, cs3)

  return image_front, image_back

if __name__ == '__main__':
  path = "C:/temp/jacq-suite/data/P1374_D1694"

  program = cv.imread(path+"/pattern/program.png", flags=cv.IMREAD_UNCHANGED)
  program = cv.cvtColor(program, cv.COLOR_BGRA2RGBA)

  front, back  = render(program)

  cv.imwrite(path+"/pattern/texture_front.png", cv.cvtColor(front, cv.COLOR_RGBA2BGRA))
  cv.imwrite(path+"/pattern/texture_back.png", cv.cvtColor(back, cv.COLOR_RGBA2BGRA))
