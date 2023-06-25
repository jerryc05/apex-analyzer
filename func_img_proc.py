import numpy as np
import cv2


def black_area(img: np.ndarray[int, np.dtype[np.uint8]]):  # 阴影面积
    return len(np.where(img == 0)[0])


def white_area(img: np.ndarray[int, np.dtype[np.uint8]]):  # 白区面积
    return len(np.where(img == 255)[0])


def img_similarity(
    img1: np.ndarray[int, np.dtype[np.uint8]], img2: np.ndarray[int, np.dtype[np.uint8]]
):
    comp = img1 == img2
    sim = len(np.where(comp == True)[0])
    return sim


def scale_image(
    img: "np.ndarray[int, np.dtype[np.uint8]]", scale: float
) -> np.ndarray[int, np.dtype[np.uint8]]:  # 缩放
    _w = int(img.shape[1] * scale)
    _h = int(img.shape[0] * scale)
    return cv2.resize(img, (_w, _h))
