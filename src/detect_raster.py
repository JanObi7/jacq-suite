import numpy as np
import cv2 as cv

img = cv.imread('recolored_part.jpg')
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
blurred = cv.GaussianBlur(gray, (3,3), 0)
edges = cv.Canny(blurred, 50, 150, apertureSize=3) # Passe die Schwellenwerte an

lines = cv.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=5)
# Parameter Erklärung:
# 1: Rho-Auflösung in Pixeln
# np.pi / 180: Theta-Auflösung in Radianten (1 Grad)
# 100: Schwellenwert (Minimum an Schnittpunkten in der Hough-Ebene, um eine Linie zu erkennen)
# minLineLength: Minimale Länge einer Linie in Pixeln
# maxLineGap: Maximaler Abstand zwischen zwei Punkten einer Linie, um sie noch als eine Linie zu betrachten

horizontal_lines = []
vertical_lines = []

if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Berechne den Winkel in Radianten und konvertiere zu Grad
        angle_rad = np.arctan2(y2 - y1, x2 - x1)
        angle_deg = np.abs(np.degrees(angle_rad))

        # Toleranz für horizontale und vertikale Linien
        angle_tolerance = 5 # Grad

        if (angle_deg < angle_tolerance) or (angle_deg > 180 - angle_tolerance):
            horizontal_lines.append((x1, y1, x2, y2))
        elif (angle_deg > 90 - angle_tolerance) and (angle_deg < 90 + angle_tolerance):
            vertical_lines.append((x1, y1, x2, y2))

intersection_points = []
output_img = img.copy() # Für die Visualisierung der Schnittpunkte

# Eine Funktion zum Zeichnen von Linien (optional, zur Visualisierung)
def draw_line(img, line, color=(0, 0, 255), thickness=2):
    x1, y1, x2, y2 = line
    cv.line(img, (x1, y1), (x2, y2), color, thickness)

# Zeichne horizontale Linien in Rot
for h_line in horizontal_lines:
    draw_line(output_img, h_line, (0, 0, 255))

# Zeichne vertikale Linien in Blau
for v_line in vertical_lines:
    draw_line(output_img, v_line, (255, 0, 0))

# Berechne Schnittpunkte
for h_line in horizontal_lines:
    x1_h, y1_h, x2_h, y2_h = h_line # y1_h und y2_h sollten sehr nah beieinander liegen
    
    for v_line in vertical_lines:
        x1_v, y1_v, x2_v, y2_v = v_line # x1_v und x2_v sollten sehr nah beieinander liegen
        
        # Vereinfachte Annahme für perfekte horizontale/vertikale Linien
        # Verwende den mittleren Y-Wert für die horizontale Linie
        intersect_y = (y1_h + y2_h) / 2
        # Verwende den mittleren X-Wert für die vertikale Linie
        intersect_x = (x1_v + x2_v) / 2

        # Überprüfe, ob der Schnittpunkt innerhalb der Liniensegmente liegt
        # Für horizontale Linie: x_schnitt muss zwischen min(x1,x2) und max(x1,x2) liegen
        # Für vertikale Linie: y_schnitt muss zwischen min(y1,y2) und max(y1,y2) liegen
        
        # Toleranz hinzufügen für schwankende Linienenden
        x_min_h, x_max_h = min(x1_h, x2_h), max(x1_h, x2_h)
        y_min_v, y_max_v = min(y1_v, y2_v), max(y1_v, y2_v)

        if (x_min_h - 5 <= intersect_x <= x_max_h + 5) and \
           (y_min_v - 5 <= intersect_y <= y_max_v + 5): # Toleranz von 5 Pixeln
            
            intersection_points.append((int(intersect_x), int(intersect_y)))
            cv.circle(output_img, (int(intersect_x), int(intersect_y)), 1, (0, 255, 255), -1) # Gelber Kreis

cv.imshow('Erkannte Linien und Schnittpunkte', output_img)
cv.waitKey(0)
cv.destroyAllWindows()

print(f"Anzahl erkannter Schnittpunkte: {len(intersection_points)}")