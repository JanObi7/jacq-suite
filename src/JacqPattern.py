import cv2 as cv
import numpy as np

def edit(pattern, dk, ds):
  ns, nk = np.shape(pattern)

  bs = int(ns/ds)
  bk = int(nk/dk)

  selecting = False
  s1 = -1
  s2 = -1
  k1 = -1
  k2 = -1
  smin = -1
  smax = -1
  kmin = -1
  kmax = -1
  csmin = -1
  csmax = -1
  ckmin = -1
  ckmax = -1

  z = 10

  def showPattern():

    # build image
    image = cv.resize(pattern, (z*bk, z*bs))
    image = cv.cvtColor(image, cv.COLOR_GRAY2BGR)

    for s in range(bs):
      cv.line(image, (0,z*s), (z*bk, z*s), (0,0,0), 1)
    for k in range(bk):
      cv.line(image, (z*k,0), (z*k, z*bs), (0,0,0), 1)

    cv.rectangle(image, (z*kmin, z*smin), (z*kmax+z, z*smax+z), (255,255,0))
    cv.rectangle(image, (z*ckmin, z*csmin), (z*ckmax+z, z*csmax+z), (0,255,0))

    cv.imshow("pattern", image)

  def handle_event(event,x,y,flags,param):
    nonlocal selecting, s1, s2, k1, k2, smin, smax, kmin, kmax

    if event == cv.EVENT_LBUTTONDOWN:
      if not selecting:
        s = int(y / z)
        k = int(x / z)

        selecting = True
        s1 = s
        s2 = s
        k1 = k
        k2 = k

        showPattern()

    if event == cv.EVENT_MOUSEMOVE:
      if selecting:
        s = int(y / z)
        k = int(x / z)

        k2 = k
        s2 = s

        showPattern()

    if event == cv.EVENT_LBUTTONUP:
      if selecting:
        selecting = False

    if s2 >= s1:
      smin = s1
      smax = s2
    else:
      smin = s2
      smax = s1

    if k2 >= k1:
      kmin = k1
      kmax = k2
    else:
      kmin = k2
      kmax = k1

  cv.namedWindow('pattern')
  cv.setMouseCallback('pattern', handle_event)

  showPattern()

  while True:
    k = cv.waitKey(20) & 0xFF

    if k == ord('c'):
      csmin = smin
      csmax = smax
      ckmin = kmin
      ckmax = kmax
      s1 = -1
      s2 = -1
      k1 = -1
      k2 = -1
      smin = -1
      smax = -1
      kmin = -1
      kmax = -1
    
      showPattern()
      
    if k == ord('v'):
      cs = csmax - csmin + 1
      ck = ckmax - ckmin + 1
      vs = smax - smin + 1
      vk = kmax - kmin + 1

      print (cs, ck, vs, vk)

      if vk % ck == 0 and vs % cs == 0:
        print("passt")

        for s in range(int(vs/cs)):
          for k in range(int(vk/ck)):
            pattern[ds*(smin+s*cs):ds*(smin+s*cs+cs), dk*(kmin+k*ck):dk*(kmin+k*ck+ck)] = pattern[ds*(csmin):ds*(csmin+cs), dk*(ckmin):dk*(ckmin+ck)]

      csmin = -1
      csmax = -1
      ckmin = -1
      ckmax = -1
      s1 = -1
      s2 = -1
      k1 = -1
      k2 = -1
      smin = -1
      smax = -1
      kmin = -1
      kmax = -1
    
      showPattern()
      
    if k == 27:
      break

  cv.destroyAllWindows()

  return pattern

def render(pattern, dk, ds):
  ns, nk = np.shape(pattern)

  # build image
  image = np.zeros((dk*ns+400, ds*nk+400, 3), np.uint8)

  # set paper color
  image[:,:] = (200,220,220)

  # set red fields
  for k in range(nk):
    for s in range(ns):
      if pattern[ns-s-1,k] == 0:
        image[200+dk*(ns-s-1):200+dk*(ns-s), 200+ds*k:200+ds*k+ds] = (0,0,200)
      elif pattern[ns-s-1,k] == 127:
        image[200+dk*(ns-s-1):200+dk*(ns-s), 200+ds*k:200+ds*k+ds] = (200,100,100)

  # draw grey horizontal lines
  for s in range(ns+1):
    image[200+dk*s:200+dk*s+1, 200:200+ds*nk] = (120,120,120)

  # draw grey vertical lines
  for k in range(nk+1):
    image[200:200+dk*ns, 200+ds*k:200+ds*k+1] = (120,120,120)

  # draw black horizontal lines
  for s in range(ns+1):
    if s % ds == 0:
      image[200+dk*s:200+dk*s+1, 200:200+ds*nk] = (20,20,20)

  # draw black vertical lines
  for k in range(nk+1):
    if k % dk == 0:
      image[200:200+dk*ns, 200+ds*k:200+ds*k+1] = (20,20,20)
    
  # draw chain numbers
  for k in range(nk+1):
    if k % (2*dk) == 0:
      text = "1" if k == 0 else str(k)
      (sx, sy), bl = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
      cv.putText(image, text, (int(200+ds*k-sx/2), 180), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
      cv.putText(image, text, (int(200+ds*k-sx/2), 230+dk*ns), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
    
  # draw shot numbers
  for s in range(ns+1):
    if s % (2*ds) == 0:
      text = "1" if s == 0 else str(s)
      (sx, sy), bl = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
      cv.putText(image, text, (int(190-sx), 207+dk*(ns-s)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
      cv.putText(image, text, (int(210+ds*nk), 207+dk*(ns-s)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv.LINE_AA)
    

  return image
