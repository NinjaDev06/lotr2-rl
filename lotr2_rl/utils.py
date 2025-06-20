import numpy as np
import imagehash
from PIL import Image
import cv2

def hash_image(img: Image) -> str:
    return imagehash.average_hash(img)

def is_same_image(img1: Image, ref_hash: str, threshold: int = 1) -> bool:
    # Hamming distance
    dist = hash_image(img1) - ref_hash
    return dist < threshold



class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"
        

def search_image(large_image, small_image) -> list[Point]:
    # Match template
    result = cv2.matchTemplate(large_image, small_image, cv2.TM_CCOEFF_NORMED)

    threshold = 0.8
    boxes = np.where(result >= threshold)
    locations = []
    for pt in zip(*boxes[::-1]):
        loc = Point(pt[0] + small_image.shape[0]//2, pt[1] + small_image.shape[1]//2)
        locations.append(loc)
    
    return locations

def is_image_present(large_image, small_image) -> bool:
    result = cv2.matchTemplate(large_image, small_image, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    return np.any(result >= threshold)
