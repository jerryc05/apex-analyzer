# coding=UTF-8
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
from func_input_videos import input_videos
from damage_ocr import dmg_area_select


def capture_nonzerodmg_imgs() -> None:
    video_path = input_videos()[0]
    capture = cv2.VideoCapture(str(video_path))
    original_data_path = Path('./Temp/readdata_original.feather')
    original_data = pd.read_feather(str(original_data_path)).values
    FRAMES = original_data[:, 0:1]
    WEAPONS = original_data[:, 1:2]
    AMMOS = original_data[:, 2:3]
    DAMAGES = original_data[:, 3:4]
    total_frames = len(FRAMES)
    destdir1 = Path('./Temp/key_capture')
    destdir1.mkdir(exist_ok=True)
    destdir2 = Path('./Temp/key_dmg')
    destdir2.mkdir(exist_ok=True)
    for frame_num in range(total_frames):
        if DAMAGES[frame_num, 0]:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, img_bgr = capture.read()
            assert ret, f'Error reading image in frame {frame_num}!'
            cv2.imwrite(
                str(destdir1)
                + '/'
                + str(frame_num)
                + '_'
                + str(DAMAGES[frame_num, 0])
                + '.png',
                img_bgr,
            )
            cv2.imwrite(
                str(destdir2)
                + '/'
                + str(frame_num)
                + '_'
                + str(DAMAGES[frame_num, 0])
                + '.png',
                dmg_area_select(img_bgr),
            )


if __name__ == '__main__':
    capture_nonzerodmg_imgs()
