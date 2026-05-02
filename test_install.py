print("=" * 60)
print("TEST FINAL - FACELOCK AVEC INSIGHTFACE")
print("=" * 60)

try:
    import cv2
    print("✅ OpenCV :", cv2.__version__)
except Exception as e:
    print("❌ OpenCV :", e)

try:
    import numpy
    print("✅ NumPy :", numpy.__version__)
except Exception as e:
    print("❌ NumPy :", e)

try:
    import insightface
    print("✅ insightface :", insightface.__version__)
except Exception as e:
    print("❌ insightface :", e)

try:
    import onnxruntime
    print("✅ onnxruntime :", onnxruntime.__version__)
except Exception as e:
    print("❌ onnxruntime :", e)

try:
    import customtkinter
    print("✅ customtkinter :", customtkinter.__version__)
except Exception as e:
    print("❌ customtkinter :", e)

print("=" * 60)
print("Test terminé !")