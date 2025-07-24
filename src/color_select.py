import numpy as np
import cv2 as cv
import json

###################################################################
class ColorSelector:
  def collectProbes(self, image):
    probes = []
    h, w, _ = image.shape
    x0 = int(w/2)
    y0 = int(h/2)
    m = 500

    def mouse_event(event,x,y,flags,param):
      if event == cv.EVENT_LBUTTONUP:
        xi = x0-m + x
        yi = y0-m + y
        bgr = image[yi,xi]
        probes.append(bgr.tolist())


    cv.namedWindow('select')
    cv.setMouseCallback('select', mouse_event)

    while True:
      x1 = max(x0-m, 0)
      x2 = min(x0+m, w)
      y1 = max(y0-m, 0)
      y2 = min(y0+m, h)

      selection = image[y1:y2,x1:x2].copy()
      cv.putText(selection, f"{len(probes)}", (10, 2*m-10), cv.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 4, cv.LINE_AA)
      mean = np.mean(probes, 0) if len(probes)>0 else (255,255,255)
      selection[10:110,10:110] = np.full((100, 100, 3), mean)
      cv.rectangle(selection, (10,10), (110,110), (0,0,0), 2)
      cv.imshow("select", selection)

      k = cv.waitKey(10)

      # Okay mit RETURN
      if k == 13:
        break

      if k == 8:
        probes = []

      if k == ord('a'):
        x0 = max(x0-100, m)
      if k == ord('d'):
        x0 = min(x0+100, w-m)
      if k == ord('w'):
        y0 = max(y0-100, m)
      if k == ord('s'):
        y0 = min(y0+100, h-m)

    cv.destroyAllWindows()

    return probes

def recolor_image_to_palette(img_bgr, color_palette):
    """
    Färbt ein Bild so um, dass jedes Pixel der ähnlichsten Farbe in einer gegebenen Palette entspricht.

    Args:
        image_path (str): Der Pfad zum Eingabebild.
        color_palette (list): Eine Liste von RGB-Farbtupeln (z.B. [(255, 0, 0), (0, 255, 0)]).

    Returns:
        numpy.ndarray: Das re-kolorierte Bild.
    """
    # Konvertiere die Farbpalette in ein NumPy-Array für effiziente Berechnungen
    color_palette_np = np.array(color_palette, dtype=np.float32)

    # Initialisiere ein leeres Bild für die Ausgabe
    recolored_img = np.zeros_like(img_bgr)

    # Reshape des Bildes zu einer Liste von Pixeln (Höhe * Breite, 3)
    # Dies ermöglicht eine effizientere Berechnung der Distanzen für alle Pixel gleichzeitig
    pixels = img_bgr.reshape(-1, 3).astype(np.float32)

    # Berechne die euklidische Distanz für jedes Pixel zu jeder Farbe in der Palette
    # expand_dims fügt eine neue Dimension hinzu, um Broadcasting zu ermöglichen
    # Die Form wird (Anzahl_Pixel, 1, 3) - (1, Anzahl_Farben, 3) = (Anzahl_Pixel, Anzahl_Farben, 3)
    # Die Summe über Achse 2 (die Farbkomponenten) ergibt die quadratische euklidische Distanz
    distances = np.sum((pixels[:, np.newaxis, :] - color_palette_np[np.newaxis, :, :])**2, axis=2)

    # Finde den Index der nächsten Farbe für jedes Pixel
    # argmin gibt den Index des Minimums entlang einer Achse zurück
    nearest_color_indices = np.argmin(distances, axis=1)

    # Weise die nächste Farbe dem entsprechenden Pixel zu
    # Wir greifen auf die Farbpalette mit den gefundenen Indizes zu
    recolored_pixels = color_palette_np[nearest_color_indices]

    # Reshape des re-kolorierten Pixel-Arrays zurück in die ursprüngliche Bildform
    recolored_img_bgr = recolored_pixels.reshape(img_bgr.shape).astype(np.uint8)

    return recolored_img_bgr

def createPalette(image):
  selector = ColorSelector()
  palette = []
  while True:
    probes = selector.collectProbes(image)
    if len(probes)>0:
      color = np.mean(probes, 0).astype(np.uint8).tolist()
      palette.append(color)
    else:
      break
  return palette

if __name__ == '__main__':
  
  image = cv.imread("data/D4442_P2367/scans/00000252.tif.original.jpg")

  palette = createPalette(image)
  with open("palette1.json", "w") as fp:
    json.dump(palette, fp, indent=2)

  with open("palette1.json", "r") as fp:
    palette = json.load(fp)
  print(palette)

  recolored = recolor_image_to_palette(image, palette)

  cv.imshow("result", cv.resize(recolored, None, fx=0.25, fy=0.25))
  cv.waitKey()

  cv.imwrite("recolored.jpg", recolored)
