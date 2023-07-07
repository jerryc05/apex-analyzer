import numpy as np
import cv2
import pytesseract
from PIL import Image
from func_img_proc import scale_image

# DMGCUT:L1750,R1830,L95,H120
# Img_Damage = IMG[94:120,1749:1835]
DMG_REF = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
DMG_NUM = list()
for _p in range(10):
    DMG_NUM.append(cv2.imread('./Ref/Damage/' + str(_p) + '.png', 0))
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
    if len(img_cut.shape) > 2:
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
    # print('Max Simulation: {}'.format(np.max(res)))
    return img_cut[:, loc + w_ref :]


def split_dmg_digits(img: np.ndarray[int, np.dtype[np.uint8]]) -> list():  # 分割数字到每一位
    # img_cut = img[9:-4, :]  # 裁切上下白边
    img_cut = img
    empty_detector = np.min(img_cut, axis=0)
    _ret = list()
    _renew = True
    if np.min(empty_detector) == 255:
        return _ret  # 没有数字
    blackarea_index = np.where(empty_detector == 0)[0]
    _first_index = blackarea_index[0]
    _last_index = blackarea_index[0]
    for _index in blackarea_index:
        if _renew:  # 刷新
            _first_index = _index
            _last_index = _index
            _renew = False
        if not _renew and _index - _last_index < 2:  # 连续
            _last_index = _index
        if not _renew and _index - _last_index >= 2:  # 出现断点
            _ret.append(img_cut[:, _first_index : _last_index + 1])
            _renew = True
    if not _renew:
        _ret.append(img_cut[:, _first_index : _last_index + 1])
    return _ret


def dmg_digit_recognize(
    img: np.ndarray[int, np.dtype[np.uint8]]
) -> int | None:  # 单位数字识别
    assert len(img.shape) == 2, 'Input image channel error!'
    _h, _w = img.shape
    if _w > 10 or _w < 2:  # 噪点或多位数字
        return None
    # 判1!
    img_hstacked = np.hstack(
        (255 * np.ones([_h, 2], dtype=np.uint8), img, 255 * np.ones([_h, 2], dtype=np.uint8))
    )
    for _p in range(10):
        max_sim = np.max(cv2.matchTemplate(img_hstacked, DMG_NUM[_p], cv2.TM_CCOEFF_NORMED))
        print('{} similarity: {}'.format(_p, max_sim))


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


# developing new algorithm
from pathlib import Path


def convert_train_img() -> None:
    sourcedir = Path('./Temp/train')
    destdir = Path('./Temp/train_dmg')
    destdir.mkdir(parents=True, exist_ok=True)
    cnt = 0
    for img_path in sourcedir.rglob('*.jpg'):
        img_gray = cv2.imread(str(img_path), 0)
        print('Processing Img {}'.format(cnt + 1))
        img_cut = cut_dmg_logo_match_tpl(dmg_area_select(img_gray, False))
        if img_cut.size:
            _output = str(destdir) + '/' + str(cnt) + '.png'
            cnt += 1
            cv2.imwrite(_output, img_cut)
    print('{} images converted successfully!'.format(cnt))


def post_process_img(
    img_cut: np.ndarray[int, np.dtype[np.uint8]]
) -> np.ndarray[int, np.dtype[np.uint8]]:
    if len(img_cut.shape) > 2:
        img_cut = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((2, 2), np.uint8)
    dilation = cv2.dilate(img_cut, kernel, iterations=1)
    erosion = cv2.erode(dilation, kernel, iterations=1)
    return erosion


def post_convert_train_img() -> None:
    sourcedir = Path('./Temp/train_dmg')
    destdir = Path('./Temp/post_train_dmg')
    destdir.mkdir(parents=True, exist_ok=True)
    cnt = 0
    for img_path in sourcedir.rglob('*.png'):
        img_gray = cv2.imread(str(img_path), 0)
        img_processed = post_process_img(img_gray)
        img_cut = img_processed[9:-4, :]
        cnt += 1
        cv2.imwrite(str(destdir) + '/' + str(cnt) + '.png', img_cut)
    print('{} images post-converted successfully!'.format(cnt))


def split_train_img() -> None:
    sourcedir = Path('./Temp/post_train_dmg')
    destdir = Path('./Temp/split_train_dmg')
    destdir.mkdir(parents=True, exist_ok=True)
    cnt = 0
    for img_path in sourcedir.rglob('*.png'):
        img_gray = cv2.imread(str(img_path), 0)
        img_series = split_dmg_digits(img_gray)
        _i = 0
        cnt += 1
        for img in img_series:
            _i += 1
            cv2.imwrite(str(destdir) + '/' + str(cnt) + '_' + str(_i) + '.png', img)


def main() -> None:
    img_gray = cv2.imread('./Temp/split_train_dmg/20_2.png', 0)  # 4
    dmg_digit_recognize(img_gray)


if __name__ == '__main__':
    main()
