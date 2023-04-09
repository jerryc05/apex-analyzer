import numpy as np
import cv2
import pytesseract
from PIL import Image

# DMGCUT:L1750,R1830,L95,H120
# Img_Damage = IMG[94:120,1749:1835]
# cv2.imshow('DMG',Img_Damage)
# cv2.waitKey(0)
DmgRef = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
h, w = np.shape(DmgRef)
pytesseract.pytesseract.tesseract_cmd = 'D:/Program Files/Tesseract-OCR/tesseract.exe'


def dmg_area_select(Img, Rank=False):
    if Rank:
        return Img[94:120, 1675:1761]
    return Img[94:120, 1749:1835]  # 裁剪


def cut_dmg_logo_classic(Img_Cut):
    Img_Cut = cv2.threshold(Img_Cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    Img_Cut = cv2.cvtColor(Img_Cut, cv2.COLOR_BGR2GRAY)
    H, W = np.shape(Img_Cut)
    sim = np.zeros([W - w, 1])
    for i in range(W - w):
        comp = DmgRef == Img_Cut[:, i : i + w]
        sim[i, 0] = len(np.where(comp == True)[0])
    Logofit = np.where(sim[:, 0] == np.max(sim[:, 0]))[0][0]
    return Img_Cut[:, Logofit + w :]


def cut_dmg_logo_match_tpl(Img_Cut):
    Img_Cut = cv2.threshold(Img_Cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    Img_Cut = cv2.cvtColor(Img_Cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(Img_Cut, DmgRef, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    return Img_Cut[:, loc + w :]


def get_damage(img, Rank=False) -> int:
    Img_Cut = dmg_area_select(img, Rank=Rank)
    Img_DmgNum = cut_dmg_logo_match_tpl(Img_Cut)
    if Img_DmgNum.shape[1] == 0:
        return 0
    cv2.imwrite('./Temp/temp_damage.png', Img_DmgNum)
    Text_Damage = pytesseract.image_to_string(Image.open('./Temp/temp_damage.png'), lang='num')
    Text_Damage = ''.join(filter(str.isdigit, Text_Damage))
    if len(Text_Damage):
        return int(Text_Damage)
    return 0


def damage_correction(Damage_fixed, Damage_read):  # 修正策略
    if Damage_read > Damage_fixed + 400:
        return Damage_fixed
    return max(Damage_fixed, Damage_read)


if __name__ == '__main__':
    Img = cv2.imread('./Temp/TrainSource/1059_sourceG1 (70).png')
    img = cv2.cvtColor(Img, cv2.COLOR_BGR2GRAY)
    Img_Cut = Img[94:120, 1675:1761]
    Img_DmgNum = cut_dmg_logo_classic(Img_Cut)
    cv2.imwrite('./Temp/classicoutput.png', Img_DmgNum)
    Img_Cut = cv2.threshold(Img_Cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_Cut = cv2.cvtColor(Img_Cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_Cut, DmgRef, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    DmgNum_1 = img_Cut[:, loc + w :]
    cv2.imwrite('./Temp/newoutput.png', DmgNum_1)
