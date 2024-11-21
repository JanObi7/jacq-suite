import cv2 as cv
import numpy as np
import csv

def buildCards(path):
  program = cv.imread(path+"/pattern/program.png")
  pattern = cv.cvtColor(program, cv.COLOR_BGRA2RGBA)
  ns, nk, _ = np.shape(pattern)

  # prepare headers
  headers = ['name']

  # card with 2 x 440er blocks
  for c in range(56):
    for r in range(16):
      if not (c in [0,1,26,27,28,29,54,55] and r in [7,8]):
        headers.append(f'dot_{c+1}_{r+1}')

  # generate cards
  cards = []

  # A cards
  for s in range(ns):
    card = { "name": f"A{(s+1):03d}" }

    for k in range(880):
      dot = headers[1+k]

      # set dot for A (k: 1 - 880)
      color = tuple(pattern[ns-s-1,k].tolist())
      if color == (255,0,0,255):
        card[dot] = 1
      else:
        card[dot] = 0

    cards.append(card)

  # B cards
  for s in range(ns):
    card = { "name": f"B{(s+1):03d}" }

    for k in range(880):
      dot = headers[1+k]

      # set dot for B (k: 881 - 1760)
      color = tuple(pattern[ns-s-1,880+k].tolist())
      if color == (255,0,0,255):
        card[dot] = 1
      else:
        card[dot] = 0

    cards.append(card)

  # write cards
  with open(path+"/cards/cards.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter=';')

    writer.writeheader()
    for card in cards:
      writer.writerow(card)


def readCards(path):
  # read cards
  cards = []

  with open(path+'/cards/cards.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for card in reader:
      cards.append(card)

  return cards

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
    for c in range(28):
      for r in range(16):
        # block 1
        dot = f'dot_{c+1}_{r+1}'
        if dot in card:
          if card[dot] == "1":
            cv.circle(image, (m+50+20+20*c, m+20+20*r), 7, (0,0,0), -1, cv.LINE_AA)

        # block 2
        dot = f'dot_{28+c+1}_{r+1}'
        if dot in card:
          if card[dot] == "1":
            cv.circle(image, (m+50+580+20+20*c, m+20+20*r), 7, (0,0,0), -1, cv.LINE_AA)

    # write card label
    cv.putText(image, card["name"], (m+5,m+15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (50,50,50), 1, cv.LINE_AA)

    # save image
    cv.imwrite(path+f"/cards/{card["name"]}.png", image)
