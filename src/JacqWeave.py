import numpy as np
import cv2 as cv

################################################################################################
def render(program, config):
  ns, nk, _ = np.shape(program)

  width = config["width"]
  height = config["height"]

  # build image
  image_front = np.zeros((height, width, 3), np.uint8)
  image_back = np.zeros((height, width, 3), np.uint8)

  # helper
  def lighten(color, percent):
    return (
      int(color[0]/100*(100+percent)),
      int(color[1]/100*(100+percent)),
      int(color[2]/100*(100+percent)),
    )

  # getter and setter
  def get(k, s):
    return tuple(program[ns-1-s%ns, k%nk].tolist()) == (255, 0, 0, 255)

  # color getter
  def getShot(s):
    n = len(config["shots"])
    i = int(s/n)
    for id, shot in config["shots"][s%n].items():
      if id == "*": return config["colors"][shot["color"]], shot["width"]

  def getChain(k):
    n = len(config["chains"])
    i = int(k/n)
    for id, chain in config["chains"][k%n].items():
      if id == "*":
        return config["colors"][chain["color"]], chain["width"]
      elif ":" in id:
        i1, i2 = id.split(":")
        if i >= int(i1)-1 and i <= int(i2)-1:
          return config["colors"][chain["color"]], chain["width"]


  # def bindings(s):
  #   # zählt die Abbindungen wo sich zwei nebeneinander liegende (0 oder 1 Abstand) Kettfäden kreuzen
  #   b = 0
  #   for k in range(nk):
  #     b11 = get(k,s)
  #     b12 = get(k,s+1)
  #     b21 = get(k+1,s)
  #     b22 = get(k+1,s+1)
  #     b31 = get(k+2,s)
  #     b32 = get(k+2,s+1)
  #     if b11 and not b12 and (not b21 and b22):
  #       b += 1
  #     if not b11 and b12 and (b21 and not b22):
  #       b += 1
  #   return b
  
  def bindings(s):
    # zählt die Abbindungen wo sich zwei nebeneinander liegende (0 oder 1 Abstand) Kettfäden kreuzen
    b = 0
    for k in range(nk):
      b11 = get(k,s)
      b12 = get(k,s+1)
      b21 = get(k+1,s)
      b22 = get(k+1,s+1)
      b31 = get(k+2,s)
      b32 = get(k+2,s+1)
      if b11 and not b12 and (not b21 and b22 or not b31 and b32):
        b += 1
      if not b11 and b12 and (b21 and not b22 or b31 and not b32):
        b += 1
    return b
  
  # iterate over pattern
  fach_shots = 0

  fy = 0
  s = 0
  while fy < height:
    fx = 0
    for k in range(nk):

      def draw_front(x, y, c, o):
        if o == "v" and x >= 5:
          image_front[height-fy-y:height-fy, fx:fx+x] = lighten(c, -25)
          image_front[height-fy-y:height-fy, fx+1:fx+x-1] = lighten(c, 0)
          image_front[height-fy-y:height-fy, fx+2:fx+x-2] = lighten(c, 10)
        elif o == "h" and y >= 7:
          image_front[height-fy-y:height-fy, fx:fx+x] = lighten(c, -25)
          image_front[height-fy-y+1:height-fy-2, fx:fx+x] = lighten(c, 0)
          image_front[height-fy-y+2:height-fy-4, fx:fx+x] = lighten(c, 10)
        else:
          image_front[height-fy-y:height-fy, fx:fx+x] = c


      def draw_back(x, y, c, o):
        if o == "v" and x >= 5:
          image_back[height-fy-y:height-fy, width-fx-x:width-fx] = lighten(c, -25)
          image_back[height-fy-y:height-fy, width-fx-x+1:width-fx-1] = lighten(c, 0)
          image_back[height-fy-y:height-fy, width-fx-x+2:width-fx-2] = lighten(c, 10)
        elif o == "h" and y >= 7:
          image_back[height-fy-y:height-fy, width-fx-x:width-fx] = lighten(c, -25)
          image_back[height-fy-y+1:height-fy-2, width-fx-x:width-fx] = lighten(c, 0)
          image_back[height-fy-y+2:height-fy-4, width-fx-x:width-fx] = lighten(c, 10)
        else:
          image_back[height-fy-y:height-fy, width-fx-x:width-fx] = c


      if fach_shots == 1:
        ck, wk = getChain(k)
        cs1, ws = getShot(s-1)
        cs2, ws = getShot(s)

        b1 = get(k, s-1)
        b2 = get(k, s)
        br1 = get(k+1, s-1)
        br2 = get(k+1, s)
        brr1 = get(k+2, s-1)
        brr2 = get(k+2, s)

        if b1 and not b2:
          draw_front(wk,ws,cs2,"h")
          draw_back(wk,ws,cs1,"h")
        elif not b1 and b2:
          draw_front(wk,ws,cs1,"h")
          draw_back(wk,ws,cs2,"h")
        elif b1 and b2:
          draw_front(wk,ws,ck,"v")
          if br1 and not br2:
            draw_back(wk,ws,cs1,"h")
          elif not br1 and br2:
            draw_back(wk,ws,cs2,"h")
          elif brr1 and not brr2:
            draw_back(wk,ws,cs1,"h")
          elif not brr1 and brr2:
            draw_back(wk,ws,cs2,"h")
          else:
            draw_back(wk,ws,cs1,"h")
        elif not b1 and not b2:
          draw_back(wk,ws,ck,"v")
          if br1 and not br2:
            draw_front(wk,ws,cs2,"h")
          elif not br1 and br2:
            draw_front(wk,ws,cs1,"h")
          elif brr1 and not brr2:
            draw_front(wk,ws,cs2,"h")
          elif not brr1 and brr2:
            draw_front(wk,ws,cs1,"h")
          else:
            draw_front(wk,ws,cs2,"h")

        
      else:
        ck, wk = getChain(k)
        cs, ws = getShot(s)

        if get(k, s):
          draw_front(wk,ws,ck,"v")
          draw_back(wk,ws,cs,"h")
        else:
          draw_front(wk,ws,cs,"h")
          draw_back(wk,ws,ck,"v")

      # weiter in x Richtung
      fx += wk

    # weiter in y Richtung
    if bindings(s)/nk >= 0.1:
      fy += ws
      fach_shots = 0
    else:
      fach_shots += 1
      print("fach", fach_shots)

    # next shot
    s += 1

  return image_front, image_back

################################################################################################
def render_1694(program, config, dx, dy):
  ns, nk, _ = np.shape(program)

  nx = int(nk/3)
  ny = int(ns/3)

  # build image
  image_front = np.zeros((dx*ny, dy*nx, 3), np.uint8)
  image_back = np.zeros((dx*ny, dy*nx, 3), np.uint8)

  # helper
  def lighten(color, percent):
    return (
      int(color[0]/100*(100+percent)),
      int(color[1]/100*(100+percent)),
      int(color[2]/100*(100+percent)),
    )

  # getter and setter
  def get(k, s):
    return tuple(program[ns-1-s%ns, k%nk].tolist()) == (255, 0, 0, 255)

  # color getter
  def getShot(s):
    n = len(config["shots"])
    i = int(s/n)
    for id, shot in config["shots"][s%n].items():
      if id == "*": return config["colors"][shot["color"]], shot["width"]

  def getChain(k):
    n = len(config["chains"])
    i = int(k/n)
    for id, chain in config["chains"][k%n].items():
      if id == "*":
        return config["colors"][chain["color"]], chain["width"]
      elif ":" in id:
        i1, i2 = id.split(":")
        if i >= int(i1)-1 and i <= int(i2)-1:
          return config["colors"][chain["color"]], chain["width"]

  # iterate over pattern
  for y in range(ny):
    for x in range(nx):
      def set_front(xmin, xmax, ymin, ymax, c):
        image_front[dx*ny-1-dx*y-ymax-1:dx*ny-1-dx*y-ymin, dy*x+xmin:dy*x+xmax+1] = c

      def set_back(xmin, xmax, ymin, ymax, c):
        image_back[dx*ny-1-dx*y-ymax-1:dx*ny-1-dx*y-ymin, dy*nx-1-dy*x-xmax-1:dy*nx-1-dy*x-xmin] = c

      cs1, ws1 = getShot(3*y)
      cs2, ws2 = getShot(3*y+1)
      cs3, ws3 = getShot(3*y+2)

      ck1, wk1 = getChain(3*x)
      ck2, wk2 = getChain(3*x+1)
      ck3, wk3 = getChain(3*x+2)

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
