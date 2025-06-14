import cv2 as cv
import numpy as np
import json
from math import pow, sqrt, atan2, sin, cos

def readCards(path):
  with open(path+"/cards.json", 'r') as jsonfile:
    cards = json.load(jsonfile)
  return cards

def writeCards(path, cards):
  with open(path+"/cards.json", 'w') as jsonfile:
    json.dump(cards, jsonfile)

# create a cards
def createCard(name, type, dots, ctrl):
  card = { "name": name, "type": type, "data": [] }

  # init data with zeros
  if type == "880":
    for x in range(61):
      row = []
      for y in range(16):
        row += [0]
      card["data"] += [row]

    # set ctrl data
    card["data"][0] = ctrl
  
    # set dots data
    x = 2
    y = 0
    for dot in dots:
      if dot == 1:
        card["data"][x][y] = 1

      # next dot
      y += 1

      # skip fixing holes
      if x in [2,3,28,29,31,32,57,58] and y == 7:
        y += 2

      # next row
      if y >= 16:
        x += 1
        y -= 16

      # skip binding rows
      if x in [1,30,59]:
        x += 1

  return card

def buildCards(path):
  program = cv.imread(path+"/program.png")
  pattern = cv.cvtColor(program, cv.COLOR_BGRA2RGBA)
  ns, nk, _ = np.shape(pattern)

  # generate cards
  cardsA = []
  cardsB = []

  for s in range(ns):
    # Leistensteuerung
    if s%2 == 0: ctrl = [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    else: ctrl = [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    # read data from program
    dotsA = []
    dotsB = []
    for k in range(880):
      dotsA.append(1 if tuple(pattern[ns-s-1,k].tolist()) == (255,0,0,255) else 0)
      dotsB.append(1 if tuple(pattern[ns-s-1,880+k].tolist()) == (255,0,0,255) else 0)

    # build and append A and B cards
    cardsA.append(createCard(f"A{(s+1):03d}", "880", dotsA, ctrl))
    cardsB.append(createCard(f"B{(s+1):03d}", "880", dotsB, ctrl))

  # write cards
  writeCards(path, cardsA+cardsB)

def renderCards(path):
  # read cards
  cards = readCards(path)

  for card in cards:
    
    # build image
    m = 20
    image = np.zeros((m+340+m, m+50+580+580+50+m, 3), np.uint8)

    # set background
    image[m:m+340,m:m+1260] = (105,126,157)

    # set binding holes
    for x in [50,50+580,50+580+580]:
      for y in [50, 110, 230, 290]:
        cv.circle(image, (m+x, m+y), 7, (0,0,0), -1, cv.LINE_AA)

    # set fixing holes
    for x in [50+30,50+580-30,50+580+30,50+580+580-30]:
      cv.circle(image, (m+x, m+170), 15, (0,0,0), -1, cv.LINE_AA)

    # set data holes
    for x in range(60):
      for y in range(16):
        if card["data"][x][y] == 1:
          cv.circle(image, (m+50-20+20*x, m+20+20*y), 7, (0,0,0), -1, cv.LINE_AA)

    # write card label
    cv.putText(image, card["name"], (m+5,m+15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (50,50,50), 1, cv.LINE_AA)

    # save image
    cv.imwrite(path+f"/cards/{card["name"]}.png", image)

def readStamps(path):
  with open(path+"/stamps.json", 'r') as jsonfile:
    return json.load(jsonfile)

def writeStamps(path, cards):
  with open(path+"/stamps.json", 'w') as jsonfile:
    json.dump(cards, jsonfile)

def nearestPoint(points, x, y):
  min_dist = 10e6
  nearest = None
  for xh, yh in points:
    dist = sqrt(pow(x-xh,2) + pow(y-yh,2))
    if dist < min_dist:
      nearest = (xh, yh)
      min_dist = dist
  return nearest

def scanStamp(path, name, ref=None):
  card = None
  warp = None

  width = 5 * 254
  height = 5 * 70
  margin = 20

  cam = cv.VideoCapture(0, cv.CAP_DSHOW)
  cam.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
  cam.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
  cam.set(cv.CAP_PROP_AUTOFOCUS, 255)

  while True:
    _, image = cam.read()

    # rotate image
    image = cv.rotate(image, cv.ROTATE_180)

    # try to find card contour
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    _, thresh = cv.threshold(gray, 150, 255, cv.THRESH_BINARY)
    contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # cv.imshow("gray", gray)
    # cv.drawContours(image, contours, -1, (0,0,255),1)

    # look for card contour
    card = None
    for cnt in contours:
      (xc, yc), radius = cv.minEnclosingCircle(cnt)
      if radius > 350 and radius < 450:
        card = cv.approxPolyDP(cnt, 10, True)
        break

    # find tholes and dholes inside the card
    tholes = []
    dholes = []
    if card is not None and len(card) == 4:
      for cnt in contours:
        (x, y), r = cv.minEnclosingCircle(cnt)
        if cv.pointPolygonTest(card, (x,y), False) >= 0:
          if r > 8 and r < 11:
            tholes.append((x, y))
          elif r > 4 and r < 8:
            dholes.append((x, y))

      # sort tholes from left to right
      tholes = sorted(tholes, key=lambda hole: hole[0])
    
    if len(tholes) == 4:
      # get transformation from left and right tholes
      xl, yl = tholes[0]
      xr, yr = tholes[3]

      dist = sqrt(pow(xr-xl,2) + pow(yr-yl,2))
      ppmm = dist / 220 # Abstand 220 mm

      x0 = (xr+xl)/2
      y0 = (yr+yl)/2
      a = atan2(yr-yl, xr-xl)

      # calc real and image points from outer binding holes
      zoom = 5
      width = zoom * 254
      height = zoom * 70
      margin = 20

      coords = [(-116, -24), (-116, +24), (+116, -24), (+116, +24)]
      sources = []
      targets = []

      for xr, yr in coords:
          dx = ppmm*xr*1.01
          dy = ppmm*yr
          x = x0 + dx*cos(a) - dy*sin(a)
          y = y0 + dx*sin(a) + dy*cos(a)
          xh, yh = nearestPoint(dholes, x, y)

          sources.append([xh, yh])
          targets.append([(2*margin+width)/2 + zoom*xr, (2*margin+height)/2 + zoom*yr])

      matrix = cv.getPerspectiveTransform(np.float32(sources), np.float32(targets))
      warp = cv.warpPerspective(image, matrix, (2*margin+width, 2*margin+height))

      # find holes in transformed image
      image = warp.copy()
      gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
      _, thresh = cv.threshold(gray, 150, 255, cv.THRESH_BINARY)
      contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

      bholes = []
      dholes = []
      for cnt in contours:
        (x, y), r = cv.minEnclosingCircle(cnt)
        if r > 5 and r < 10:
          # filter out binding holes
          isbhole = False
          for xh, yh in [(-116, -24), (-116, -12), (-116, 12), (-116, 24), (0, -24), (0, -12), (0, 12), (0, 24), (116, -24), (116, -12), (116, 12), (116, 24) ]:
            if cv.pointPolygonTest(cnt, ((2*margin+width)/2 + zoom*xh, (2*margin+height)/2 + zoom*yh), False) >= 0:
              isbhole = True
              break
          if not isbhole:
            dholes.append(cnt)

      # cv.drawContours(image, dholes, -1, (0,0,255), 1)

      data = []
      for i in range(0,60):
        row = []
        for j in range(0,16):
          x = (2*margin+width)/2 + zoom*4*i - zoom*120
          y = (2*margin+height)/2 + zoom*4*j - zoom*30

          match = False
          for cnt in dholes:
            if cv.pointPolygonTest(cnt, (x,y), False) >= 0:
              match = True
              break

          row.append(1 if match else 0)

          if ref:
            color = (0, 255, 0) if match and ref["data"][i][j] == 1 or not match and ref["data"][i][j] == 0 else (0,0,255)
          else:
            color = (255,255,255) if match else (0,0,0)

          cv.circle(image, (int(x), int(y)), 7, color, 1)

        data.append(row)

      # create card
      card = {
        "name": name,
        "type": "880",
        "data": data,
      }
      

    cv.imshow("image", image)

    k = cv.waitKey(1)

    # Abbruch mit ESCAPE
    if k == 27:
      break
  
    # Okay mit RETURN
    if k == 13:
      if warp is not None:
        cv.imwrite(path+f"/stamps/{name}.png", warp)

      if card is not None:
        stamps = [card]
        for stamp in readStamps(path):
          if stamp["name"] != name:
            stamps.append(stamp)
        writeStamps(path, stamps)

      break

  cv.destroyAllWindows()
  cam.release()


def compareCards(card1, card2):
  passes = 0
  errors = 0

  for i in range(0,60):
    for j in range(0,16):
      if card1["data"][i][j] == card2["data"][i][j]:
        passes += 1
      else:
        errors += 1
        print(f"error at {i},{j}: data1 {card1["data"][i][j]}, data2 {card2["data"][i][j]}")

  print("passes:", passes)
  print("errors:", errors)
  print(f"error rate: {errors/(errors+passes)*100} %")


if __name__ == "__main__":
  path = "d:/temp/jacq-suite/data/TH913_3523"
  name = "A040"

  scanStamp(path, name)

  cards = readCards(path)
  stamps = readStamps(path)

  for card in cards:
    if card["name"] == name: break
  for stamp in stamps:
    if stamp["name"] == name: break

  compareCards(card, stamp)