import numpy as np


def black_area(img):  # 阴影面积
    return len(np.where(img == 0)[0])


def white_area(img):  # 白区面积
    return len(np.where(img == 255)[0])


def img_similarity(img1, img2):
    comp = img1 == img2
    sim = len(np.where(comp == True)[0])
    return sim
