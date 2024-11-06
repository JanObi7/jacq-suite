import numpy as np
import cv2 as cv


img = np.zeros((100,200,4), dtype=np.uint8)

cv.rectangle(img, (10,10), (90,90), (255,0,0,255), -1)

mask = np.zeros((100,200), dtype=np.uint8)
cv.circle(mask, (100,50), 25, 255, -1)

img[mask==255] = (0,0,0,0)

cv.imshow("img", img)
cv.imshow("mask", mask)
# cv.imshow("crop", crop)

cv.waitKey()