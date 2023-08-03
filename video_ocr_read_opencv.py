# coding=UTF-8
# 读入视频，输出识别未处理数据报表
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple, cast

import cv2
import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm
import multiprocessing as mp

import weapon_dict
from ammo_ocr import ammo_recognize_cv
from weapon_recognize import weapon_recognize
from func_input_videos import input_videos


def get_total_frames(video_path: Path) -> int:
    capture = cv2.VideoCapture(str(video_path))
    return int(capture.get(cv2.CAP_PROP_FRAME_COUNT))


def read_apex_video(
    video_path: Path,
    output_original_data: Path,
    start_frame: int | None = None,
    end_frame: int | None = None,
    process_id: int = 0,
):
    if not video_path.is_file():
        raise ValueError(f'Error: video_path [{video_path}] is not a file!')
    # pyright: ignore[reportUnknownMemberType]
    capture: Any = cv2.VideoCapture(str(video_path))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    _p_frame = 0
    if start_frame is None or end_frame is None:
        end_frame = total_frames
        start_frame = 0
    frame_num = start_frame
    total_frames = end_frame - start_frame
    FRAMES = np.zeros([total_frames, 1], dtype=np.uint16)
    WEAPONS = np.zeros([total_frames, 1], dtype=np.object_)
    AMMOS = np.zeros([total_frames, 1], dtype=np.object_)
    DAMAGES = np.zeros([total_frames, 1], dtype=np.uint16)
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    desc = str(video_path) + ' ' + str(start_frame) + '-' + str(end_frame)
    with tqdm(total=total_frames, desc=desc, position=process_id, leave=False) as pbar:
        pbar.update(_p_frame)
        while frame_num < end_frame:
            weapon = None
            ammo = None
            damage = 0
            # try:

            ret, img_bgr = cast(Tuple[bool, npt.NDArray[np.uint8]], capture.read())
            assert type(ret) == bool
            if not ret:
                break
            assert img_bgr.dtype == np.uint8
            # except:
            #     print('read error, jumping......')
            #     frame_num += 100
            #     capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            #     continue
            weapon, wpsim = weapon_recognize(img_bgr)
            if weapon:
                ammo_maxdigits = weapon_dict.weapon_dict[weapon].max_ammo_digits
                ammo = ammo_recognize_cv(img_bgr, ammo_maxdigits)
            WEAPONS[_p_frame, 0] = weapon
            AMMOS[_p_frame, 0] = ammo
            DAMAGES[_p_frame, 0] = damage
            FRAMES[_p_frame, 0] = frame_num
            frame_num += 1
            _p_frame += 1
            pbar.update(_p_frame - pbar.n)
    WEAPONS = WEAPONS[0:_p_frame, :]
    AMMOS = AMMOS[0:_p_frame, :]
    DAMAGES = DAMAGES[0:_p_frame, :]
    FRAMES = FRAMES[0:_p_frame, :]
    ori_dtf = pd.DataFrame(
        np.hstack((FRAMES, WEAPONS, AMMOS, DAMAGES)),
        columns=['FRAME', 'WEAPON', 'AMMO', 'DAMAGE'],
    )
    if output_original_data.suffix == '.xls':
        ori_dtf.to_excel(output_original_data, index=False)
    if output_original_data.suffix == '.feather':
        ori_dtf.to_feather(output_original_data)
    return FRAMES, WEAPONS, AMMOS, DAMAGES, _p_frame, fps


def main():
    vid_path = input_videos()[0][0]
    output_original_data = Path('./Temp/readdata_original.feather')
    tic = datetime.now()
    read_apex_video(video_path=vid_path, output_original_data=output_original_data)
    toc = datetime.now()
    print(f'Elapsed time: { (toc - tic).total_seconds()} seconds')


if __name__ == '__main__':
    main()
