import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Tuple, cast
import numpy.typing as npt
import cv2
import re
from ammo_ocr import ammo_recognize_cv
from weapon_recognize import weapon_recognize
import weapon_dict
from damage_ocr import get_damage_match_tpl
from tqdm import tqdm


def bullet_capture(weapon: str = '*') -> None:
    bigdata_path = Path('./BigData/BigData_FiringList.xlsx')
    assert bigdata_path.is_file(), 'No available input!'
    bigdata = pd.read_excel(str(bigdata_path)).values
    bullet_list = []
    with tqdm(total=len(bigdata)) as pbar:
        for _p in range(len(bigdata)):
            pbar.update(_p)
            if re.search(weapon, bigdata[_p, 3]):  # 名称匹配
                video_path = Path(bigdata[_p, 0])
                start_frame = int(bigdata[_p, 1])
                end_frame = int(bigdata[_p, 2])
                _discard_flag = True  # 去除每段视频的第一发
                _ammo_before = -1
                _damage_before = -1
                _weapon_using = False
                _temp_list = []
                _start_frame = -1
                _end_frame = -1
                capture = cv2.VideoCapture(str(video_path))
                capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                for _capture_p in range(start_frame, end_frame + 1):
                    ret, img_bgr = cast(Tuple[bool, npt.NDArray[np.uint8]], capture.read())
                    assert ret, 'No image!'
                    if not _weapon_using:
                        weapon, wpsim = weapon_recognize(img_bgr)
                        if weapon:
                            ammo_maxdigits = weapon_dict.weapon_dict[weapon].max_ammo_digits
                            bps = weapon_dict.weapon_dict[weapon].bullets_per_shot
                            _weapon_using = True
                    ammo = ammo_recognize_cv(img_bgr, ammo_maxdigits)
                    if _ammo_before == -1:  # 未登录
                        _ammo_before = ammo
                        _start_frame = _capture_p
                        _damage_before = get_damage_match_tpl(img_bgr)
                    if ammo != _ammo_before:  # 减少了，保存整段
                        if ammo is None:
                            ammo = _ammo_before - bps
                        _end_frame = _capture_p
                        _damage_after = get_damage_match_tpl(img_bgr)
                        if ammo == _ammo_before - bps or ammo == _ammo_before:
                            _temp_list.append(
                                [
                                    str(video_path),
                                    _start_frame,
                                    _end_frame,
                                    weapon,
                                    _ammo_before - ammo,
                                    _damage_after - _damage_before,
                                    _ammo_before,
                                    ammo,
                                ]
                            )
                        _start_frame = _capture_p
                        _damage_before = _damage_after
                        _ammo_before = ammo
                        if _discard_flag:
                            _temp_list = []
                            _discard_flag = False
                if end_frame != _start_frame:
                    _damage_after = get_damage_match_tpl(img_bgr)
                    _temp_list.append(
                        [
                            str(video_path),
                            _start_frame,
                            end_frame,
                            weapon,
                            0,
                            _damage_after - _damage_before,
                            _ammo_before,
                            _ammo_before,
                        ]
                    )  # 最后一段
                bullet_list.extend(_temp_list)
            pbar.update(_p + 1 - pbar.n)
    dtf = pd.DataFrame(
        bullet_list,
        columns=[
            'Video_Name',
            'Start_Frame',
            'End_Frame',
            'Used_Weapon',
            'Used_Ammo',
            'Damage_Dealt',
            'Ammo_Before',
            'Ammo_After',
        ],
    )
    dtf.to_excel('./BigData/bullet_list.xlsx', index=None)


if __name__ == '__main__':
    bullet_capture('CAR')
