import numpy as np
import cv2
import pytesseract
from PIL import Image

# DMGCUT:L1750,R1830,L95,H120
# Img_Damage = IMG[94:120,1749:1835]
# cv2.imshow('DMG',Img_Damage)
# cv2.waitKey(0)
DMG_REF = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
DMG_REF = cv2.imread('F:/CodeProject/APEX_ANALYZER/Ref/DmgLogo/DmgLogo.png', 0)
h, w = np.shape(DMG_REF)
pytesseract.pytesseract.tesseract_cmd = 'D:/Program Files/Tesseract-OCR/tesseract.exe'


def dmg_area_select(img, rank_league=None):
    if rank_league == None:
        return img[94:120, 1675:1835]
    if rank_league:
        return img[94:120, 1675:1761]
    return img[94:120, 1749:1835]  # 裁剪


def cut_dmg_logo_classic(img):
    img_cut = cv2.threshold(img, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_cut = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    H, W = np.shape(img_cut)
    sim = np.zeros([W - w, 1])
    for i in range(W - w):
        comp = DMG_REF == img_cut[:, i : i + w]
        sim[i, 0] = len(np.where(comp == True)[0])
    logo_fit = np.where(sim[:, 0] == np.max(sim[:, 0]))[0][0]
    return img_cut[:, logo_fit + w :]


def cut_dmg_logo_match_tpl(img):
    img_cut = cv2.threshold(img, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_cut = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_cut, DMG_REF, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    return img_cut[:, loc + w :]


def get_damage(img, rank_league=None) -> int:
    img_cut = dmg_area_select(img, rank_league=rank_league)
    img_dmgnum = cut_dmg_logo_match_tpl(img_cut)
    if img_dmgnum.shape[1] == 0:
        return 0
    cv2.imwrite('./Temp/temp_damage.png', img_dmgnum)
    text_damage = pytesseract.image_to_string(Image.open('./Temp/temp_damage.png'), lang='num')
    text_damage = ''.join(filter(str.isdigit, text_damage))
    if len(text_damage):
        return int(text_damage)
    return 0


def damage_correction(damage_fixed: int, damage_read: int) -> int:  # 修正策略
    if damage_read > damage_fixed + 400:
        return damage_fixed
    return max(damage_fixed, damage_read)


if __name__ == '__main__':
    img_bgr = cv2.imread('# Your APEX Video Screenshot')
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_cut = img_bgr[94:120, 1675:1761]
    img_dmgnum = cut_dmg_logo_classic(img_cut)
    cv2.imwrite('./Temp/classicoutput.png', img_dmgnum)
    img_cut = cv2.threshold(img_cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_cut_1 = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_cut_1, DMG_REF, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    dmgnum_1 = img_cut_1[:, loc + w :]
    cv2.imwrite('./Temp/newoutput.png', dmgnum_1)
