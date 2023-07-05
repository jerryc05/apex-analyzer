import numpy as np
import cv2
import pytesseract
from PIL import Image
from func_img_proc import scale_image

# DMGCUT:L1750,R1830,L95,H120
# Img_Damage = IMG[94:120,1749:1835]
DMG_REF = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
h_ref, w_ref = np.shape(DMG_REF)
pytesseract.pytesseract.tesseract_cmd = 'D:/Program Files/Tesseract-OCR/tesseract.exe'


def dmg_area_select(
    img: np.ndarray[int, np.dtype[np.uint8]], rank_league: bool | None = None
) -> np.ndarray[int, np.dtype[np.uint8]]:
    _h = img.shape[0]
    _w = img.shape[1]
    assert isinstance(_h, int)
    assert isinstance(_w, int)
    img_cut = img[94:120, 1675:1835]  # default
    if _h == 1080 and _w == 1920:  # 1080P 16:9
        img_cut = img[94:120, 1675:1835]
    if _h == 1600 and _w == 2560:  # 2K 16:10
        img_cut = scale_image(img[125:160, 2222:2435], 0.75)
    if rank_league == None:  # 是否排位未知
        return img_cut
    if rank_league:  # 排位
        return img_cut[:, 0:86]
    return img_cut[:, 74:]  # 非排位


def cut_dmg_logo_classic(
    img: np.ndarray[int, np.dtype[np.uint8]]
) -> np.ndarray[int, np.dtype[np.uint8]]:
    img_cut = cv2.threshold(img, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_cut = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    _h, _w = np.shape(img_cut)
    sim = np.zeros([_w - w_ref, 1])
    for i in range(_w - w_ref):
        comp = DMG_REF == img_cut[:, i : i + w_ref]
        sim[i, 0] = len(np.where(comp == True)[0])
    logo_fit = np.where(sim[:, 0] == np.max(sim[:, 0]))[0][0]
    return img_cut[:, logo_fit + w_ref :]


def cut_dmg_logo_match_tpl(
    img: np.ndarray[int, np.dtype[np.uint8]]
) -> np.ndarray[int, np.dtype[np.uint8]]:
    img_cut = cv2.threshold(img, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    if len(img_cut.shape) > 2:
        img_cut = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_cut, DMG_REF, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    return img_cut[:, loc + w_ref :]


def get_damage(
    img: np.ndarray[int, np.dtype[np.uint8]], rank_league: bool | None = None
) -> int:
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


def main() -> None:
    img_bgr = cv2.imread('# Your APEX Video Screenshot')
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_cut = img_bgr[94:120, 1675:1761]
    img_dmgnum = cut_dmg_logo_classic(img_cut)
    cv2.imwrite('./Temp/classicoutput.png', img_dmgnum)
    img_cut = cv2.threshold(img_cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    img_cut_1 = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_cut_1, DMG_REF, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res == np.max(res))[1][0]  # xtick
    dmgnum_1 = img_cut_1[:, loc + w_ref :]
    cv2.imwrite('./Temp/newoutput.png', dmgnum_1)


from pathlib import Path


def convert_train_img() -> None:
    sourcedir = Path('./Temp/train')
    destdir = Path('./Temp/train_dmg')
    cnt = 1
    for img_path in sourcedir.rglob('*.jpg'):
        img_gray = cv2.imread(str(img_path), 0)
        img_cut = cut_dmg_logo_match_tpl(dmg_area_select(img_gray, False))
        _output = str(destdir) + '/' + str(cnt) + '.png'
        cv2.imwrite(_output, img_cut)
        cnt += 1
    print('{} images convert successfully!'.format(cnt))


if __name__ == '__main__':
    convert_train_img()
