# coding=UTF-8
import os

import cv2
import numpy as np
import numpy.typing as npt
import pandas as pd

from func_cv_imread import cv_imread
from func_cv_imwrite import cv_imwrite, cv_imwrite_png
from func_img_proc import black_area, img_similarity

# LR1541-1696 HL958-996


def cut_weapon(img: np.ndarray[int,np.dtype[np.uint8]]) -> np.ndarray[int,np.dtype[np.uint8]]:  # 裁剪
    return img[958:996, 1541:1696]


def binary_weapon(img: np.ndarray[int,np.dtype[np.uint8]]) -> np.ndarray[int,np.dtype[np.uint8]]:  # 二值化
    return cv2.threshold(img, 225, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化


def dilate_weapon(img: np.ndarray[int,np.dtype[np.uint8]]) -> np.ndarray[int,np.dtype[np.uint8]]:  # 膨胀
    kernel = np.ones((3, 3), np.uint8)
    dilation = cv2.dilate(img, kernel, iterations=1)
    return dilation


def erode_weapon(img: np.ndarray[int,np.dtype[np.uint8]]) -> np.ndarray[int,np.dtype[np.uint8]]:  # 腐蚀
    kernel = np.ones((3, 3), np.uint8)
    erosion = cv2.erode(img, kernel, iterations=1)
    return erosion


def weapon_img_process(img: np.ndarray[int, np.dtype[np.uint8]]):
    assert img.dtype == np.uint8
    if img.ndim > 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = binary_weapon(cut_weapon(img))
    img = erode_weapon(img)
    return img


def weapon_ref_generate():  # 生成参考
    sourcefiledir = './Ref/Weapons_Original/'
    destfiledir = './Ref/Weapons/'
    for source in os.listdir(sourcefiledir):
        img_bgr = cv_imread(sourcefiledir + source)
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_cut = cut_weapon(img)
        img_cut = binary_weapon(img_cut)
        img_cut = erode_weapon(img_cut)
        cv2.imencode('.png', img_cut)[1].tofile(
            destfiledir + source[:-4] + '.png'
        )  # 中文路径保存


def weapon_ref_evaluate():  # 参考互相比较
    filedir = './Ref/Weapons/'
    maxn = len(os.listdir(filedir))
    similarity = np.zeros([maxn, maxn])
    black_area = np.zeros([maxn, 1])
    i = 0
    j = 0
    for file_img1 in os.listdir(filedir):
        img1 = cv_imread(filedir + file_img1)
        # img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        for file_img2 in os.listdir(filedir):
            img2 = cv_imread(filedir + file_img2)
            # img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            sim = img_similarity(img1, img2)
            # print('{} vs. {}: {}'.format(file_img1, file_img2, sim))
            similarity[i, j] = sim
            j += 1
        black_area[i, 0] = len(np.where(img1 == 0)[0])
        i += 1
        j = 0
    print(np.mean(similarity))
    xd = pd.DataFrame(similarity)
    xd.to_excel(
        './Ref/Weapon_Similarity.xlsx', header=os.listdir(filedir), index=os.listdir(filedir)
    )
    xd = pd.DataFrame(black_area.T)
    xd.to_excel('./Ref/Weapon_Ref_BlackArea.xlsx', header=os.listdir(filedir), index=False)


def weapon_recognize(img: np.ndarray[int, np.dtype[np.uint8]]):
    img_cut = weapon_img_process(img)
    # img = Dilate_Weapon(img)
    blackarea = black_area(img_cut)
    if blackarea < 900 or blackarea > 4200:
        return None, 0
    reffiledir = './Ref/Weapons/'
    weaponlist = os.listdir(reffiledir)
    i = 0
    similarity = np.empty((len(weaponlist), 1))
    for filename in weaponlist:
        IMG_REF = cv_imread(reffiledir + filename)
        sim = img_similarity(img_cut, IMG_REF)
        similarity[i, 0] = sim
        # if sim > 5000:
        #     return filename, sim
        i += 1
    maxsimnum = int(np.max(similarity))
    maxsimname = weaponlist[np.where(similarity == np.max(similarity))[0][0]]
    if maxsimnum < 5100:
        return None, maxsimnum
    return maxsimname[:-4], maxsimnum


if __name__ == '__main__':
    weapon_ref_generate()
    # Weapon_Ref_Evaluate()
