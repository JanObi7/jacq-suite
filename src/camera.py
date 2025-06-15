import cv2 as cv
import numpy as np
from settings import writeSetting, readSetting

cam = None

def open():
  global cam, mtx, dist

  cam = cv.VideoCapture(0, cv.CAP_DSHOW)
  cam.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
  cam.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
  cam.set(cv.CAP_PROP_AUTOFOCUS, 0)

  mtx = np.float32(readSetting("camera_matrix"))
  dist = np.float32(readSetting("camera_distance"))


def close():
  global cam
  cam.release()

def capture(undistort=True):
  global cam, mtx, dist
  _, image = cam.read()

  if undistort:
    image = cv.undistort(image, mtx, dist)

  return image

def calibrate():
  CHECKERBOARD = (7,10)
  criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

  objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
  objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

  open()

  objpoints = []
  imgpoints = [] 

  while len(objpoints) < 10:
    while True:
      image = capture(False)

      gray = cv.cvtColor(image,cv.COLOR_BGR2GRAY)
      ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_FAST_CHECK + cv.CALIB_CB_NORMALIZE_IMAGE)
      if ret == True:
        corners2 = cv.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
        cv.drawChessboardCorners(image, CHECKERBOARD, corners2, ret)

      cv.imshow("image", image)

      k = cv.waitKey(1)
    
      # Okay mit RETURN
      if k == 13:
        break

    if ret == True:
      objpoints.append(objp)
      imgpoints.append(corners2)

  cv.destroyAllWindows()
  close()

  # calc calib parameters
  ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
  
  print("Camera matrix : \n")
  print(mtx)
  print("dist : \n")
  print(dist)
  print("rvecs : \n")
  print(rvecs)
  print("tvecs : \n")
  print(tvecs)

  writeSetting("camera_matrix", mtx.tolist())
  writeSetting("camera_distance", dist.tolist())


# test code
if __name__ == "__main__":
  calibrate()
