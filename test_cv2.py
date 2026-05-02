import cv2
import numpy as np

print("OpenCV version:", cv2.__version__)
print("NumPy version:", np.__version__)

# Créer une image test
img = np.zeros((400, 600, 3), dtype=np.uint8)
img[:] = (255, 255, 255)  # Blanc

cv2.putText(img, "Test OpenCV", (200, 200), 
           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

cv2.imshow("Test", img)
print("Fenêtre ouverte. Appuyez sur une touche pour fermer...")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("✅ OpenCV fonctionne !")