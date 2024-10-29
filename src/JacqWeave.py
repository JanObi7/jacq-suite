import numpy as np

def render(pattern, dk, ds):
  ns, nk = np.shape(pattern)

  # crop
  # cs = 13*ds
  # ck = 12*dk

  # build image
  image = np.zeros((dk*ns, ds*nk, 3), np.uint8)

  # set red fields
  for s in range(ns):
    for k in range(nk):
      disp = [-50,-15,0,-15,-50] # for ds=5
      disp = [-50,0,0,-50] # for ds=4
      disp2 = [-50,-20,-5,0,0,-5,-20,-50]
      if pattern[s%ns,k] == 0:
        if pattern[(s-1)%ns,k] == 0:
          for d in range(ds):
            image[dk*s:dk*s+8, ds*k+d] = (0,0,250+disp[d])
            # image[dk*s:dk*s+8, ds*k+d] = (250+disp[d],250+disp[d],250+disp[d])
        else:
          for i in range(5):
            for d in range(ds):
              image[dk*s+i, ds*k+d] = (0,0,200+10*i+disp[d])
              # image[dk*s+i, ds*k+d] = (200+10*i+disp[d],200+10*i+disp[d],200+10*i+disp[d])
          for d in range(ds):
            image[dk*s+5:dk*s+8, ds*k+d] = (0,0,250+disp[d])
            # image[dk*s+5:dk*s+8, ds*k+d] = (250+disp[d],250+disp[d],250+disp[d])
          
        if pattern[(s+1)%ns,k] == 0:
          for d in range(ds):
            image[dk*s+8:dk*s+dk, ds*k+d] = (0,0,250+disp[d])
            # image[dk*s+8:dk*s+dk, ds*k+d] = (250+disp[d],250+disp[d],250+disp[d])
        else:
          for d in range(ds):
            image[dk*s+8:dk*s+11, ds*k+d] = (0,0,250+disp[d])
            # image[dk*s+8:dk*s+11, ds*k+d] = (250+disp[d],250+disp[d],250+disp[d])
          for i in range(5):
            for d in range(ds):
              image[dk*s+11+i, ds*k+d] = (0,0,250-10*i+disp[d])
              # image[dk*s+11+i, ds*k+d] = (250-10*i+disp[d],250-10*i+disp[d],250-10*i+disp[d])

      else:
        for d in range(8):
          image[dk*s+4+d, ds*k:ds*k+ds] = (200+disp2[d], 200+disp2[d], 200+disp2[d])

        if pattern[(s-1)%ns,k] == 255:
          for d in range(ds):
            image[dk*s:dk*s+4, ds*k+d] = (0,0,150+disp[d])
            # image[dk*s:dk*s+4, ds*k+d] = (150+disp[d],150+disp[d],150+disp[d])
        else:
          for i in range(4):
            for d in range(ds):
              image[dk*s+i, ds*k+d] = (0,0,200-12*i+disp[d])
              # image[dk*s+i, ds*k+d] = (200-12*i+disp[d],200-12*i+disp[d],200-12*i+disp[d])

        if pattern[(s+1)%ns,k] == 255:
          for d in range(ds):
            image[dk*s+12:dk*s+dk, ds*k+d] = (0,0,150+disp[d])
            # image[dk*s+12:dk*s+dk, ds*k+d] = (150+disp[d],150+disp[d],150+disp[d])
        else:
          for i in range(4):
            for d in range(ds):
              image[dk*s+12+i, ds*k+d] = (0,0,150+12*i+disp[d])
              # image[dk*s+12+i, ds*k+d] = (150+12*i+disp[d],150+12*i+disp[d],150+12*i+disp[d])


  return image
