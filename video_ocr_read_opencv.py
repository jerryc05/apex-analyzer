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

import weapon_dict
from ammo_ocr import ammo_recognize_cv
from damage_ocr import get_damage_match_tpl
from weapon_recognize import weapon_recognize


def read_apex_video(
    video_path: Path,
    output_original_data: Path,
    dmg_sample_hz: int = 1,  # 伤害查询采样率
    rank_league: bool | None = None,
):
    if not video_path.is_file():
        raise ValueError(f'Error: video_path [{video_path}] is not a file!')
    # pyright: ignore[reportUnknownMemberType]
    capture: Any = cv2.VideoCapture(str(video_path))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    dmg_sample = fps / dmg_sample_hz

    frame_num = 0

    FRAMES = np.zeros([total_frames, 1], dtype=np.uint16)
    WEAPONS = np.zeros([total_frames, 1], dtype=np.object_)
    AMMOS = np.zeros([total_frames, 1], dtype=np.object_)
    DAMAGES = np.zeros([total_frames, 1], dtype=np.uint16)

    with tqdm(total=total_frames) as pbar:
        pbar.update(frame_num)
        while True:
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
                #if int(frame_num % dmg_sample) == 0:
                #    damage = get_damage_match_tpl(img_bgr, rank_league=rank_league)
            WEAPONS[frame_num, 0] = weapon
            AMMOS[frame_num, 0] = ammo
            DAMAGES[frame_num, 0] = damage
            FRAMES[frame_num, 0] = frame_num

            # if frame_num % 2000 == 0:
            #     print(f'{frame_num} / {total_frames} frames')
            frame_num += 1
            pbar.update(frame_num - pbar.n)
    ori_dtf = pd.DataFrame(
        np.hstack((FRAMES, WEAPONS, AMMOS, DAMAGES)),
        columns=['FRAME', 'WEAPON', 'AMMO', 'DAMAGE'],
    )
    if output_original_data.suffix == '.xls':
        ori_dtf.to_excel(output_original_data, index=False)
    if output_original_data.suffix == '.feather':
        ori_dtf.to_feather(output_original_data)
    return FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps


def main():
    vid_path = Path('##your apex video')
    output_original_data = Path('./Temp/readdata_original.feather')
    tic = datetime.now()
    read_apex_video(video_path=vid_path, output_original_data=output_original_data)
    toc = datetime.now()
    print(f'Elapsed time: { (toc - tic).total_seconds()} seconds')


if __name__ == '__main__':
    main()
