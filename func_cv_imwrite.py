import cv2
import numpy as np


def cv_imwrite(filename: str, img: np.ndarray) -> None:
    cv2.imencode('.jpg', img)[1].tofile(filename)  # 中文路径保存


def cv_imwrite_png(filename: str, img: np.ndarray) -> None:
    cv2.imencode('.png', img)[1].tofile(filename)
