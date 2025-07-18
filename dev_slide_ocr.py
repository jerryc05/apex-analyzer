# coding=UTF-8
import numpy as np
import cv2
from pathlib import Path
import sys
from func_cv_imread import cv_imread
import damage_ocr as do


def input_img() -> np.ndarray[int, np.dtype[np.uint8]]:
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        img_path = Path(input())
    assert img_path.is_file(), 'Invalid file path!'
    return cv_imread(str(img_path))


def nothing(a):
    pass


def main():
    img_bgr = input_img()
    cv2.namedWindow('Val', cv2.WINDOW_AUTOSIZE)
    cv2.createTrackbar('Val', 'Val', 0, 255, nothing)
    while True:
        img_original = do.dmg_area_select(img_bgr, None)
        threshold_val = cv2.getTrackbarPos('Val', 'Val')
        img_threshold = cv2.threshold(img_original, threshold_val, 255, cv2.THRESH_BINARY_INV)[
            1
        ]
        damage_str = str(do.get_damage_match_tpl(img_bgr, threshold_val=threshold_val))
        img_processed = do.post_process_img(
            do.cut_dmg_logo_match_tpl(img_original, threshold_val=threshold_val)
        )
        d_v = img_original.shape[0] - img_processed.shape[0]
        _w = img_processed.shape[1]
        img_processed_vstk = np.vstack(
            (img_processed, 255 * np.ones([d_v, _w], dtype=np.uint8))
        )
        img_processed_vstk = cv2.cvtColor(img_processed_vstk, cv2.COLOR_GRAY2BGR)
        img_hstk = np.hstack((img_original, img_threshold, img_processed_vstk))
        cv2.imshow(str(damage_str), img_hstk)
        if cv2.waitKey(0) == 27:
            break
        cv2.destroyWindow(str(damage_str))
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
