import cv2
import numpy as np
import os
from func_cv_imread import cv_imread
from func_img_proc import img_similarity, black_area, scale_image
import pandas as pd


def cut_ammo(
    img: np.ndarray[int, np.dtype[np.uint8]]
) -> np.ndarray[int, np.dtype[np.uint8]]:  # 裁切主弹夹弹药数字
    _h = img.shape[0]
    _w = img.shape[1]
    assert isinstance(_h, int)
    assert isinstance(_w, int)
    if _h == 1080 and _w == 1920:
        return img[961:1000, 1700:1785]
    if _h == 1600 and _w == 2560:
        return scale_image(img[1440:1492, 2266:2380], 0.75)
    return img[961:1000, 1700:1785]


def binary_ammo(img: np.ndarray) -> np.ndarray:  # 弹药数字图二值化
    img_binary = cv2.threshold(img, 215, 255, cv2.THRESH_BINARY_INV)[1]
    return img_binary


def ammo_ocr_img_process(img: np.ndarray) -> np.ndarray:  # 预处理弹药数字图
    if img.ndim > 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return binary_ammo(cut_ammo(img))


def digit2(img: np.ndarray) -> np.ndarray:  # 百位数
    return img[3:34, 3:26]


def digit1(img: np.ndarray) -> np.ndarray:  # 十位数
    return img[3:34, 30:53]


def digit0(img: np.ndarray) -> np.ndarray:  # 个位数
    return img[3:34, 57:80]


def ammo_recognize_1_digit(img: np.ndarray) -> int:
    if black_area(img) < 80:
        return None
    reffiledir = './Ref/Ammo/'
    maxn = 10
    similarity = np.zeros([maxn, 1], dtype=np.uint16)
    for i in range(maxn):
        img_Ref = cv2.imread(reffiledir + str(i) + '.png', 0)
        sim = img_similarity(img, img_Ref)
        similarity[i, 0] = sim
    maxsimnum = np.max(similarity)
    maxsimname = np.where(similarity == np.max(similarity))[0][0]
    if maxsimnum < 300:
        return None
    return maxsimname


def ammo_recognize_cv(img: np.ndarray, digits: int) -> int:
    img = ammo_ocr_img_process(img)
    ammo_num = ammo_recognize_1_digit(digit0(img))
    if ammo_num is None:
        return None
    if digits > 1:
        d1 = ammo_recognize_1_digit(digit1(img))
        if d1 is not None:
            ammo_num += 10 * d1
    if digits == 3:
        d2 = ammo_recognize_1_digit(digit2(img))
        if d2 is not None:
            ammo_num += 100 * d2
    return ammo_num


if __name__ == '__main__':
    # Ammo_Train_Generate()
    pass
