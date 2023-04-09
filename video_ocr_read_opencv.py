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
    Video_Path=None, Output_Excel_Path=None, Damage_Sample_RateHZ=1, rank_league=True
):
    if Video_Path is None:
        return None
    capture = cv2.VideoCapture(Video_Path)
    total_frames = int(capture.get(7))
    fps = int(capture.get(5))
    Dmg_Sample = fps / Damage_Sample_RateHZ

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
        ret, Img = capture.read()
        if not ret:
            break
        # except:
        #     print('read error, jumping......')
        #     frame_num += 100
        #     capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        #     continue
        weapon, wpsim = weapon_recognize(Img)
        if weapon:
            ammo_maxdigits = weapon_dict.weapon_dict[weapon].max_ammo_digits
            ammo = ammo_recognize_cv(Img, ammo_maxdigits)
            if int(frame_num % Dmg_Sample) == 0:
                damage = get_damage(Img, Rank=rank_league)
        WEAPONS[frame_num, 0] = weapon
        AMMOS[frame_num, 0] = ammo
        DAMAGES[frame_num, 0] = damage
        FRAMES[frame_num, 0] = frame_num

        if frame_num % 2000 == 0:
            print('%d / %d frames' % (frame_num, total_frames))
        frame_num += 1
    if not Output_Excel_Path is None:
        xd = pd.DataFrame(np.hstack((FRAMES, WEAPONS, AMMOS, DAMAGES)))
        xd.to_excel(
            Output_Excel_Path, header=['FRAME', 'WEAPON', 'AMMO', 'DAMAGE'], index=None
        )
    return FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps


if __name__ == '__main__':
    vid_path = 'F:/MEDIA/APEX/2023-04-01 13-36-57与小溪王源爽杀C.mp4'
    output_excel = './Temp/ReadData_Original.xlsx'
    tic = datetime.now()
    read_apex_video(Video_Path=vid_path, Output_Excel_Path=output_excel)
    toc = datetime.now()
    print('Elapsed time: %f seconds' % (toc - tic).total_seconds())
