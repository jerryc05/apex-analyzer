# coding=UTF-8
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

import weapon_dict
from damage_ocr import damage_correction, get_damage_match_tpl


def apex_chart_analyze(
    video_path: Path,  # 视频路径
    FRAMES: np.ndarray,  # 视频帧数列
    WEAPONS: np.ndarray,  # 武器数列
    AMMOS: np.ndarray,  # 弹药数列
    DAMAGES: np.ndarray,  # 伤害数列
    TOTAL_FRAMES: int,  # 总帧数
    FPS: int = 60,  # 帧率,默认60
    eventchart_path: Path = None,  # 事件表路径
    fl_path: Path = None,  # 开火清单路径
    rank_league: bool = None,  # 是否排位赛，None为不识别（效率略低）
    FL_FWD_FRAME: int = 9,  # 开火提前记录帧数（而不是弹药减少了才开始记录）
    saveto_bigdata: bool = False,  # 保存至个人大数据
):
    VIDEO_NAME = video_path.name
    fl_bigdata_path = Path('./BigData/BigData_FiringList.xlsx')
    # 射击状态开关
    shooting = False
    shot_pause_flag = False  # 暂时停火状态
    shot_pause_delay_frames = 0
    SHOT_PAUSE_MAX_DELAY_FRAMES = int(1000 / (1000 / FPS) + 0.5)
    # weapon变更中间量
    weapon_temp = None  # 缓存池
    weapon_change = False  # 变更环节
    weapon_change_done = False
    weapon_change_delay_frames = 0
    WEAPON_CHANGE_MAX_DELAY_FRAMES = int(100 / (1000 / FPS) + 0.5)  # 第一个数为需要的毫秒数
    # weapon 全局量
    weapon = None
    weapon_before = None  # 上一个武器
    weapon_hold = None  # 消抖后所持
    # ammo 全局量
    ammo = None
    ammo_before = 0  # 射击前
    ammo_after = 0
    # damage 全局量
    damage = 0  # 原始OCR数据
    damage_fixed = 0  # 原始数据逻辑修正后
    damage_before = 0
    damage_dealt = 0
    damage_start_inserted = False  # 对于从中间截取的视频片段，第一次获取的非零伤害值予以采信
    DAMAGE_MAX_CHECK_FRAMES = 2
    damage_check_frames = 0
    damage_check_temp = 0

    # 开火报表
    firing_list = (
        list()
    )  # [VideoName, firing_start_f, firing_end_f, used_weapon, used_ammo, damage_dealt]
    firing_start_f = 0

    # 视频指针
    capture_p = 0
    capture_frame = cv2.VideoCapture(str(video_path))
    frame_num = 0

    txtdata = open('Temp/TempLog.txt', 'w', encoding='utf-8')

    def get_current_img() -> (
        np.ndarray[int, np.dtype[np.uint8]]
    ):  # 获取frame_num所在帧图像，为get_damage_match_tpl()做准备
        nonlocal capture_p  # opencv读图指针，如果非连续读图用capture.set重定位
        if capture_p == frame_num:
            ret, img_bgr = capture_frame.read()
        else:
            capture_frame.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, img_bgr = capture_frame.read()
        capture_p += 1
        return img_bgr

    def round_report():  # 一梭子汇报
        nonlocal shooting, shot_pause_flag, ammo_before, weapon_change_done, damage, damage_fixed, damage_dealt, damage_before, firing_list, capture_p
        # if not weapon_before:
        #     return None  # 之前没武器
        shot_ammo = ammo_before - ammo_after
        used_weapon = weapon
        if weapon_change_done:
            used_weapon = weapon_before
        # Damage Process
        img_bgr = get_current_img()
        damage = get_damage_match_tpl(img_bgr, rank_league)
        damage_fixed = damage_correction(damage_fixed, damage)
        damage_dealt = damage_fixed - damage_before
        damage_before = damage_fixed

        print(
            'frame:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
                frame_num, used_weapon, shot_ammo, damage_fixed, damage_dealt
            )
        )
        print(
            'frame:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
                frame_num, used_weapon, shot_ammo, damage_fixed, damage_dealt
            ),
            file=txtdata,
        )

        firing_list.append(
            [VIDEO_NAME, firing_start_f, frame_num, used_weapon, shot_ammo, damage_dealt]
        )
        shooting = False
        shot_pause_flag = False
        ammo_before = ammo_after

    def shot_pause():
        nonlocal shot_pause_flag, shot_pause_delay_frames
        if shot_pause_flag:
            shot_pause_delay_frames += 1
            if shot_pause_delay_frames >= SHOT_PAUSE_MAX_DELAY_FRAMES:
                shot_pause_flag = False
                shot_pause_delay_frames = 0
                return True
        else:
            shot_pause_flag = True
            shot_pause_delay_frames = 0
        return False

    print(str(video_path), file=txtdata)

    class event_chart:
        def __init__(self, total_frames: int) -> None:
            self.frame = FRAMES  # 当前帧
            self.weapon = WEAPONS
            self.ammo = AMMOS
            self.shooting = np.zeros([total_frames, 1], dtype=np.uint8)
            self.shot_pause_flag = np.zeros([total_frames, 1], dtype=np.uint8)
            self.shot_pause_delayframes = np.zeros([total_frames, 1], dtype=np.uint8)
            self.weapon_temp = np.zeros([total_frames, 1], dtype=np.object_)
            self.weapon_change = np.zeros([total_frames, 1], dtype=np.uint8)
            self.weapon_change_done = np.zeros([total_frames, 1], dtype=np.uint8)
            self.weapon_change_delayframes = np.zeros([total_frames, 1], dtype=np.uint8)
            self.weapon_before = np.zeros([total_frames, 1], dtype=np.object_)
            self.weapon_hold = np.zeros([total_frames, 1], dtype=np.object_)
            self.ammo_before = np.zeros([total_frames, 1], dtype=np.uint16)
            self.ammo_after = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage = DAMAGES
            self.damage_fixed = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage_before = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage_dealt = np.zeros([total_frames, 1], dtype=np.uint16)

    evn_chart = event_chart(total_frames=TOTAL_FRAMES)
    for frame_num in range(TOTAL_FRAMES):
        weapon = WEAPONS[frame_num, 0]
        if weapon:
            if weapon != weapon_hold:  # 装备变更控制环节
                if weapon_change:  # 在变更
                    if weapon == weapon_temp:
                        if (
                            weapon_change_delay_frames == WEAPON_CHANGE_MAX_DELAY_FRAMES
                        ):  # 消抖完成
                            weapon_before = weapon_hold
                            weapon_hold = weapon
                            weapon_temp = None
                            weapon_change_delay_frames = 0
                            weapon_change_done = True
                            weapon_change = False
                        else:  # 消抖中
                            weapon_change_delay_frames += 1
                    else:  # 被滤除
                        weapon_change_delay_frames = 0
                        weapon_change = False
                        weapon_temp = None
                else:  # 开始消抖
                    weapon_change = True
                    weapon_temp = weapon
                    weapon_change_delay_frames = 0
                if not weapon_change_done:
                    continue

            if DAMAGES[frame_num, 0] != None:  # 整秒
                damage = DAMAGES[frame_num, 0]
                if damage_check_frames:
                    if capture_p == frame_num:
                        ret, img_bgr = capture_frame.read()
                    else:
                        capture_frame.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                        ret, img_bgr = capture_frame.read()
                    capture_p += 1
                    damage = get_damage_match_tpl(img_bgr)
                    if damage_check_temp == damage:
                        damage_check_frames -= 1
                        if damage_check_frames == 0:
                            damage_start_inserted = True
                            damage_fixed = damage
                    else:
                        damage_check_temp = damage
                        damage_check_frames = DAMAGE_MAX_CHECK_FRAMES
                if not damage_start_inserted and damage and damage_check_frames == 0:
                    damage_check_frames = DAMAGE_MAX_CHECK_FRAMES
                    damage_check_temp = damage
                damage_fixed = damage_correction(damage_fixed, damage)
                if not shooting:
                    damage_before = damage_fixed
            ammo = AMMOS[frame_num, 0]
            if ammo != None:
                # Sign up: Obtain, Reload, Change
                if weapon_change_done:  # 换了
                    print('weapon changed')
                    print('weapon changed', file=txtdata)
                    # Calculate Last Weapon Damage
                    if shooting:
                        round_report()
                    shooting = False  # 换武器的一刻不可能在射击
                    # Sign up
                    ammo_before = ammo
                    ammo_after = ammo
                else:  # 没换
                    # Shoot
                    if ammo < ammo_after:  # 子弹少了
                        bps = weapon_dict.weapon_dict[
                            weapon
                        ].bullets_per_shot  # 三重3，滋蹦2，其余1
                        if ammo_after - ammo <= bps:  # 可能情况：射击、换枪
                            ammo_after = ammo
                            if not weapon_change:
                                if not shooting:
                                    firing_start_f = (
                                        frame_num - FL_FWD_FRAME
                                    )  # 记录开火开始时间
                                shooting = True
                                shot_pause_flag = False
                        else:  # 可能情况：换枪、换子弹
                            if shooting:
                                round_report()
                            if weapon_change:
                                ammo_before = ammo_after
                            elif ammo == 0:  # 换子弹会先清零
                                print('megazine clear')
                                print('megazine clear', file=txtdata)
                                ammo_after = ammo
                    elif ammo > ammo_after:  # 再装填
                        print('reloading')
                        print('reloading', file=txtdata)
                        if shooting:
                            round_report()
                        ammo_after = ammo
                        ammo_before = ammo
                    else:
                        # 停火计时
                        if shooting:
                            if shot_pause():
                                print('end shot')
                                print('end shot', file=txtdata)
                                round_report()

        # Record EventChart
        # EvnChart.ammo[frame_num,0] = ammo
        evn_chart.ammo_after[frame_num, 0] = ammo_after
        evn_chart.ammo_before[frame_num, 0] = ammo_before
        # EvnChart.frame[frame_num,0] = frame_num
        evn_chart.shooting[frame_num, 0] = shooting
        evn_chart.shot_pause_delayframes[frame_num, 0] = shot_pause_delay_frames
        evn_chart.shot_pause_flag[frame_num, 0] = shot_pause_flag
        # EvnChart.weapon[frame_num,0] = weapon
        evn_chart.weapon_before[frame_num, 0] = weapon_before
        evn_chart.weapon_hold[frame_num, 0] = weapon_hold
        evn_chart.weapon_temp[frame_num, 0] = weapon_temp
        evn_chart.weapon_change[frame_num, 0] = weapon_change
        evn_chart.weapon_change_delayframes[frame_num, 0] = weapon_change_delay_frames
        evn_chart.weapon_change_done[frame_num, 0] = weapon_change_done
        evn_chart.damage[frame_num, 0] = damage
        evn_chart.damage_fixed[frame_num, 0] = damage_fixed
        evn_chart.damage_before[frame_num, 0] = damage_before
        evn_chart.damage_dealt[frame_num, 0] = damage_dealt
        # End Loop
        if weapon_change_done:
            weapon_change_done = False
    txtdata.close()

    evn_m = np.zeros([TOTAL_FRAMES, 18], dtype=np.object_)
    evn_m[:, 0] = evn_chart.frame[:, 0]
    evn_m[:, 1] = evn_chart.ammo[:, 0]
    evn_m[:, 2] = evn_chart.ammo_before[:, 0]
    evn_m[:, 3] = evn_chart.ammo_after[:, 0]
    evn_m[:, 4] = evn_chart.shooting[:, 0]
    evn_m[:, 5] = evn_chart.shot_pause_flag[:, 0]
    evn_m[:, 6] = evn_chart.shot_pause_delayframes[:, 0]
    evn_m[:, 7] = evn_chart.weapon[:, 0]
    evn_m[:, 8] = evn_chart.weapon_hold[:, 0]
    evn_m[:, 9] = evn_chart.weapon_before[:, 0]
    evn_m[:, 10] = evn_chart.weapon_temp[:, 0]
    evn_m[:, 11] = evn_chart.weapon_change[:, 0]
    evn_m[:, 12] = evn_chart.weapon_change_done[:, 0]
    evn_m[:, 13] = evn_chart.weapon_change_delayframes[:, 0]
    evn_m[:, 14] = evn_chart.damage[:, 0]
    evn_m[:, 15] = evn_chart.damage_fixed[:, 0]
    evn_m[:, 16] = evn_chart.damage_before[:, 0]
    evn_m[:, 17] = evn_chart.damage_dealt[:, 0]
    evn_dtf = pd.DataFrame(
        evn_m.astype(str),
        columns=[
            'Frame',
            'Ammo',
            'AmmoBefore',
            'AmmoAfter',
            'Shooting',
            'shot_pauseflag',
            'shot_pause_delayframes',
            'Weapon',
            'WeaponHold',
            'WeaponBefore',
            'weapon_temp',
            'weapon_change',
            'weapon_changedone',
            'weapon_change_delayframes',
            'Damage',
            'damage_fixed',
            'damage_before',
            'damage_ThisRound',
        ],
    )
    if '.xls' in str(eventchart_path):  # 给Excel留个老接口XD
        evn_dtf.to_excel(
            eventchart_path,
            index=False,
        )
    if '.feather' in str(eventchart_path):
        evn_dtf.to_feather(eventchart_path)
    fl_dtf = pd.DataFrame(
        firing_list,
        columns=[
            'Video_Name',
            'Start_Frame',
            'End_Frame',
            'Used_Weapon',
            'Used_Ammo',
            'Damage_Dealt',
        ],
    )
    if '.xls' in str(fl_path):
        fl_dtf.to_excel(fl_path, index=False)
    if '.feather' in str(fl_path):
        fl_dtf.to_feather(fl_path)
    newread_dtf = pd.DataFrame(
        evn_m[:, (0, 7, 1, 14)], columns=['frame', 'weapon', 'ammo', 'damage']
    )
    newread_dtf.to_feather('./Temp/readdata_original.feather')
    if saveto_bigdata:
        try:
            fl_bigdata = pd.read_excel(fl_bigdata_path)
            fl_bigdata = fl_bigdata.append(fl_dtf, ignore_index=True)
            fl_bigdata.to_excel(fl_bigdata, index=None)
        except:
            fl_dtf.to_excel(fl_bigdata_path, index=None)


if __name__ == '__main__':
    # 如果对视频读取的结果有修改，在这里单独运行分析部分
    vid_path = '# Your APEX Video'  # Your APEX Video
    # ORIGINAL_DATA = pd.read_excel('./Temp/ReadData_Original.xlsx').values
    original_data = pd.read_feather('./Temp/readdata_original.feather').values
    FRAMES = original_data[:, 0:1]
    WEAPONS = original_data[:, 1:2]
    AMMOS = original_data[:, 2:3]
    DAMAGES = original_data[:, 3:4]
    total_frames = len(FRAMES)
    fps = 60
    EVN_CHART_PATH = './Temp/event_chart.feather'
    FL_PATH = './Temp/firing_list.feather'
    apex_chart_analyze(
        vid_path,
        FRAMES,
        WEAPONS,
        AMMOS,
        DAMAGES,
        total_frames,
        fps,
        EVN_CHART_PATH,
        FL_PATH,
        None,
    )
