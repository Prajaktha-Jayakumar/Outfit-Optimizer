import cv2
import numpy as np
from typing import Tuple


def dominant_color(image_path: str, k: int = 4) -> Tuple[Tuple[int, int, int], str]:
    """Return dominant color in BGR (OpenCV) and hex string"""
    img = cv2.imread(image_path)
    if img is None:
        return (0, 0, 0), "#000000"
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pixels = img.reshape((-1, 3)).astype(np.float32)
    
    # KMeans
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    
    counts = np.bincount(labels.flatten())
    dom = centers[counts.argmax()].astype(np.uint8)
    
    r, g, b = int(dom[0]), int(dom[1]), int(dom[2])
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    
    # Convert back to BGR tuple to keep OpenCV convention if needed
    return (b, g, r), hex_color