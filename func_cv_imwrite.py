import cv2
import numpy as np


def cv_imwrite(filename, Img):
    cv2.imencode('.jpg', Img)[1].tofile(filename)  # 中文路径保存


def cv_imwrite_png(filename, Img):
    cv2.imencode('.png', Img)[1].tofile(filename)
