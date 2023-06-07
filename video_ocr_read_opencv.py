# coding=UTF-8
# 读入视频，输出识别未处理数据报表
import numpy as np
import cv2
import pandas as pd
from weapon_recognize import weapon_recognize
import weapon_dict
from ammo_ocr import ammo_recognize_cv
from damage_ocr import get_damage

from datetime import datetime


def read_apex_video(
    video_path: str = None,
    output_original_data: str = None,
    DMG_SAMPLE_HZ: int = 1,  # 伤害查询采样率
    rank_league: bool = None,
):
    if video_path is None:
        return None
    capture = cv2.VideoCapture(video_path)
    total_frames = int(capture.get(7))
    fps = int(capture.get(5))
    dmg_sample = fps / DMG_SAMPLE_HZ

    frame_num = 0

    FRAMES = np.zeros([total_frames, 1], dtype=np.uint16)
    WEAPONS = np.zeros([total_frames, 1], dtype=np.object_)
    AMMOS = np.zeros([total_frames, 1], dtype=np.object_)
    DAMAGES = np.zeros([total_frames, 1], dtype=np.uint16)

    while True:
        weapon = None
        ammo = None
        damage = 0
        # try:
        ret, img_bgr = capture.read()
        if not ret:
            break
        # except:
        #     print('read error, jumping......')
        #     frame_num += 100
        #     capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        #     continue
        weapon, wpsim = weapon_recognize(img_bgr)
        if weapon:
            ammo_maxdigits = weapon_dict.weapon_dict[weapon].max_ammo_digits
            ammo = ammo_recognize_cv(img_bgr, ammo_maxdigits)
            if int(frame_num % dmg_sample) == 0:
                damage = get_damage(img_bgr, rank_league=rank_league)
        WEAPONS[frame_num, 0] = weapon
        AMMOS[frame_num, 0] = ammo
        DAMAGES[frame_num, 0] = damage
        FRAMES[frame_num, 0] = frame_num

        if frame_num % 2000 == 0:
            print('%d / %d frames' % (frame_num, total_frames))
        frame_num += 1
    ori_dtf = pd.DataFrame(
        np.hstack((FRAMES, WEAPONS, AMMOS, DAMAGES)),
        columns=['FRAME', 'WEAPON', 'AMMO', 'DAMAGE'],
    )
    if '.xls' in output_original_data:
        ori_dtf.to_excel(output_original_data, index=None)
    if '.feather' in output_original_data:
        ori_dtf.to_feather(output_original_data)
    return FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps


if __name__ == '__main__':
    vid_path = '##your apex video'
    output_original_data = './Temp/readdata_original.feather'
    tic = datetime.now()
    read_apex_video(video_path=vid_path, output_original_data=output_original_data)
    toc = datetime.now()
    print('Elapsed time: %f seconds' % (toc - tic).total_seconds())
