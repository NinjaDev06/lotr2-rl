import imagehash
from PIL import Image

def hash_image(img: Image) -> str:
    return imagehash.average_hash(img)

def is_same_image(img1: Image, ref_hash: str, threshold: int = 1) -> bool:
    # Hamming distance
    dist = hash_image(img1) - ref_hash
    return dist < threshold



