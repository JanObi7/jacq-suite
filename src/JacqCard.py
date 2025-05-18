import cv2 as cv
import numpy as np
import json

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
  cards = []

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
    cards.append(createCard(f"A{(s+1):03d}", "880", dotsA, ctrl))
    cards.append(createCard(f"B{(s+1):03d}", "880", dotsB, ctrl))

  # write cards
  writeCards(path, cards)

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



if __name__ == "__main__":

  buildCards("C:/temp/jacq-suite/data/TH913_3523")
  renderCards("C:/temp/jacq-suite/data/TH913_3523")