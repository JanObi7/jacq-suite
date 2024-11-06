import cv2 as cv
import numpy as np

def renderProgram(program, nk, ns, dk, ds):

  # build image
  image = np.zeros((dk*ns+400, ds*nk+400, 3), np.uint8)

  # set paper color
  image[:,:] = (200,220,220)

  # set red fields
  for k in range(nk):
    for s in range(ns):
      color = tuple(program[ns-s-1,k].tolist())
      if color == (255,0,0,255):
        image[200+dk*(ns-s-1):200+dk*(ns-s), 200+ds*k:200+ds*k+ds] = (0,0,200)
      elif color == (0,0,0,0):
        image[200+dk*(ns-s-1):200+dk*(ns-s), 200+ds*k:200+ds*k+ds] = (200,100,100)

  # draw grey horizontal lines
  for s in range(ns+1):
    image[200+dk*s:200+dk*s+1, 200:200+ds*nk] = (120,120,120)

  # draw grey vertical lines
  for k in range(nk+1):
    image[200:200+dk*ns, 200+ds*k:200+ds*k+1] = (120,120,120)

  # draw black horizontal lines
  for s in range(0,ns+1,10):
    image[200+dk*(ns-s):200+dk*(ns-s)+1, 200:200+ds*nk] = (20,20,20)

    text = "1" if s == 0 else str(s)
    (sx, sy), bl = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv.putText(image, text, (int(190-sx), 207+dk*(ns-s)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
    cv.putText(image, text, (int(210+ds*nk), 207+dk*(ns-s)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)

  # tabs for 1320
  tabs_1320 = [0,14,28,426,440,454,468, 866, 880, 894, 908, 1306, 1320]
  for i in range(1,25):
    tabs_1320.append(28+16*i)
    tabs_1320.append(468+16*i)
    tabs_1320.append(908+16*i)

  tabs_1760 = [0,14,28,426,440,454,468, 866, 880, 894, 908, 1306, 1320, 1334, 1348, 1746, 1760]
  for i in range(1,25):
    tabs_1760.append(28+16*i)
    tabs_1760.append(468+16*i)
    tabs_1760.append(908+16*i)
    tabs_1760.append(1348+16*i)

  # draw black vertical lines
  for k in tabs_1760:
    image[200:200+dk*ns, 200+ds*k:200+ds*k+1] = (20,20,20)

    text = "1" if k == 0 else str(k)
    (sx, sy), bl = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv.putText(image, text, (int(200+ds*k-sx/2), 180), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
    cv.putText(image, text, (int(200+ds*k-sx/2), 230+dk*ns), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
    

  return image
