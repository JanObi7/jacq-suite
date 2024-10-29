import cv2 as cv
import numpy as np
import csv

def buildCards(path):
  pattern = np.loadtxt(path+"/pattern/pattern.csv", np.uint8, delimiter=';')
  ns, nk = np.shape(pattern)

  # prepare headers
  headers = ['name']

  # card with 2 x 440er blocks
  for c in range(56):
    for r in range(16):
      if not (c in [0,1,26,27,28,29,54,55] and r in [7,8]):
        headers.append(f'dot_{c}_{r}')

  # generate cards
  cards = []

  for s in range(ns):

    A = { "name": f"A{(s+1):03d}" }
    B = { "name": f"B{(s+1):03d}" }

    for k in range(880):
      dot = headers[1+k]

      # set dot for A (k: 1 - 880)
      if pattern[ns-s-1,k] == 0:
        A[dot] = 1
      else:
        A[dot] = 0

      # set dot for B (k: 881 - 1760)
      if pattern[ns-s-1,880+k] == 0:
        B[dot] = 1
      else:
        B[dot] = 0

    cards.append(A)
    cards.append(B)

  # write cards
  with open(path+"/cards/cards.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter=';')

    writer.writeheader()
    for card in cards:
      writer.writerow(card)


def renderCards(path):
  # read cards
  cards = []
  with open(path+'/cards/cards.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for card in reader:
      cards.append(card)

  for card in cards:
    
    # build image
    m = 20
    image = np.zeros((m+340+m, m+50+580+580+50+m, 3), np.uint8)

    # set background
    image[m:m+340,m:m+1260] = (105,126,157)

    # set binding holes
    for x in [50,50+580,50+580+580]:
      for y in [50, 110, 230, 290]:
        cv.circle(image, (m+x, m+y), 6, (0,0,0), -1, cv.LINE_AA)

    # set fixing holes
    for x in [50+30,50+580-30,50+580+30,50+580+580-30]:
      cv.circle(image, (m+x, m+170), 16, (0,0,0), -1, cv.LINE_AA)

    # set data holes
    for c in range(28):
      for r in range(16):
        # block 1
        dot = f'dot_{c}_{r}'
        if dot in card:
          if card[dot] == "1":
            cv.circle(image, (m+50+20+20*c, m+340-20-20*r), 6, (0,0,0), -1, cv.LINE_AA)

        # block 2
        dot = f'dot_{28+c}_{r}'
        if dot in card:
          if card[dot] == "1":
            cv.circle(image, (m+50+580+20+20*c, m+340-20-20*r), 6, (0,0,0), -1, cv.LINE_AA)

    # write card label
    cv.putText(image, card["name"], (m+5,m+15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (50,50,50), 1, cv.LINE_AA)

    # save image
    cv.imwrite(path+f"/cards/{card["name"]}.png", image)
