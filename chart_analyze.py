# coding=UTF-8
import numpy as np
import pandas as pd
import cv2
import weapon_dict
from damage_ocr import get_damage, damage_correction


def apex_chart_analyze(
    Video_Path,
    FRAMES,
    WEAPONS,
    AMMOS,
    DAMAGES,
    total_frames,
    fps=60,
    EvnChartExcel_Path=None,
    FiringList_Path=None,
    rank_league=True,
    Firing_List_FwdFrame=9,
    Save_to_BigData=False,
):
    Video_Name = Video_Path.split(r'/')[-1]
    BigDataFL = './BigData/BigData_FiringList.xlsx'
    # 射击状态开关
    shooting = False
    shot_pause_flag = False  # 暂时停火状态
    shot_pause_DelayFrames = 0
    shot_pause_MaxDelayFrames = 0
    # weapon变更中间量
    weapon_temp = None  # 缓存池
    weapon_change = False  # 变更环节
    weapon_change_done = False
    weapon_change_delayframes = 0
    Weapon_Change_MaxDelayFrames = int(100 / (1000 / fps) + 0.5)  # 第一个数为需要的毫秒数
    shot_pause_MaxDelayFrames = int(1000 / (1000 / fps) + 0.5)
    # ammo变更中间量
    ammo_temp = None  # 缓存池
    # weapon 全局量
    weapon = None
    weapon_before = None  # 上一个武器
    weapon_hold = None  # 消抖后所持
    # ammo 全局量
    ammo = None
    ammo_before = 0  # 射击前
    ammo_after = 0
    shot_ammo = 0  # 打掉的子弹数
    # damage 全局量
    damage = 0  # 原始OCR数据
    damage_fixed = 0  # 原始数据逻辑修正后
    damage_before = 0
    damage_ThisRound = 0

    # 开火报表
    Firing_List = (
        list()
    )  # [VideoName, firing_start_f, firing_end_f, used_weapon, used_ammo, damage_dealt]
    firing_start_f = 0

    # 视频指针
    capture_p = 0
    capture_frame = cv2.VideoCapture(Video_Path)
    frame_num = 0

    txtdata = open('Temp/TempLog.txt', 'w', encoding='utf-8')

    def Round_Report():  # 一梭子汇报
        nonlocal shooting, shot_pause_flag, ammo_before, weapon_change_done, damage, damage_fixed, damage_ThisRound, damage_before, Firing_List, capture_p
        if not weapon_before:
            return None  # 之前没武器
        shot_ammo = ammo_before - ammo_after
        used_weapon = weapon
        if weapon_change_done:
            used_weapon = weapon_before
        # Damage Process
        if capture_p == frame_num:
            ret, Img = capture_frame.read()
        else:
            capture_frame.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, Img = capture_frame.read()
        capture_p += 1
        damage = get_damage(Img, rank_league)
        damage_fixed = damage_correction(damage_fixed, damage)
        damage_ThisRound = damage_fixed - damage_before
        damage_before = damage_fixed

        print(
            'frame:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
                frame_num, used_weapon, shot_ammo, damage_fixed, damage_ThisRound
            )
        )
        print(
            'frame:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
                frame_num, used_weapon, shot_ammo, damage_fixed, damage_ThisRound
            ),
            file=txtdata,
        )

        Firing_List.append(
            [Video_Name, firing_start_f, frame_num, used_weapon, shot_ammo, damage_ThisRound]
        )
        shooting = False
        shot_pause_flag = False
        ammo_before = ammo_after

    def Shot_Pause():
        nonlocal shot_pause_flag, shot_pause_DelayFrames
        if shot_pause_flag:
            shot_pause_DelayFrames += 1
            if shot_pause_DelayFrames >= shot_pause_MaxDelayFrames:
                shot_pause_flag = False
                shot_pause_DelayFrames = 0
                return True
        else:
            shot_pause_flag = True
            shot_pause_DelayFrames = 0
        return False

    print(Video_Path, file=txtdata)

    class Event_Chart:
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
            self.damage_ThisRound = np.zeros([total_frames, 1], dtype=np.uint16)

    EvnChart = Event_Chart(total_frames=total_frames)
    for frame_num in range(total_frames):
        weapon = WEAPONS[frame_num, 0]
        if weapon:
            if not weapon == weapon_hold:  # 不一样
                if weapon_change:  # 在变更
                    if weapon == weapon_temp:
                        if weapon_change_delayframes == Weapon_Change_MaxDelayFrames:  # 消抖完成
                            weapon_before = weapon_hold
                            weapon_hold = weapon
                            weapon_temp = None
                            weapon_change_delayframes = 0
                            weapon_change_done = True
                            weapon_change = False
                        else:  # 消抖中
                            weapon_change_delayframes += 1
                    else:  # 被滤除
                        weapon_change_delayframes = 0
                        weapon_change = False
                        weapon_temp = None
                else:  # 开始消抖
                    weapon_change = True
                    weapon_temp = weapon
                    weapon_change_delayframes = 0
                if not weapon_change_done:
                    continue

            if DAMAGES[frame_num, 0] is not None:  # 整秒
                damage = DAMAGES[frame_num, 0]
                damage_fixed = damage_correction(damage_fixed, damage)
                if not shooting:
                    damage_before = damage_fixed
            ammo = AMMOS[frame_num, 0]
            if not ammo is None:
                # Sign up: Obtain, Reload, Change

                if weapon_change_done:  # 换了
                    print('检测到换武器')
                    print('检测到换武器', file=txtdata)
                    # Calculate Last Weapon Damage
                    if shooting:
                        Round_Report()
                    shooting = False  # 换武器的一刻不可能在射击
                    # Sign up
                    ammo_before = ammo
                    ammo_after = ammo
                else:  # 没换
                    # Shoot
                    if ammo < ammo_after:  # 子弹少了
                        bps = weapon_dict.weapon_dict[weapon].bullets_per_shot  # 三重3，滋蹦2，其余1
                        if ammo_after - ammo <= bps:  # 可能情况：射击、换枪
                            ammo_after = ammo
                            if not weapon_change:
                                if not shooting:
                                    firing_start_f = frame_num - Firing_List_FwdFrame
                                shooting = True
                                shot_pause_flag = False
                        else:  # 可能情况：换枪、换子弹
                            if shooting:
                                Round_Report()
                            if weapon_change:
                                ammo_before = ammo_after
                            elif ammo == 0:  # 换子弹会先清零
                                print('清空弹仓')
                                print('清空弹仓', file=txtdata)
                                ammo_after = ammo
                    elif ammo > ammo_after:
                        print('检测到换弹')
                        print('检测到换弹', file=txtdata)
                        if shooting:
                            Round_Report()
                        ammo_after = ammo
                        ammo_before = ammo
                    else:
                        # 停火计时
                        if shooting:
                            if Shot_Pause():
                                print('检测到停火')
                                print('检测到停火', file=txtdata)
                                Round_Report()

        # Record EventChart
        # EvnChart.ammo[frame_num,0] = ammo
        EvnChart.ammo_after[frame_num, 0] = ammo_after
        EvnChart.ammo_before[frame_num, 0] = ammo_before
        # EvnChart.frame[frame_num,0] = frame_num
        EvnChart.shooting[frame_num, 0] = shooting
        EvnChart.shot_pause_delayframes[frame_num, 0] = shot_pause_DelayFrames
        EvnChart.shot_pause_flag[frame_num, 0] = shot_pause_flag
        # EvnChart.weapon[frame_num,0] = weapon
        EvnChart.weapon_before[frame_num, 0] = weapon_before
        EvnChart.weapon_hold[frame_num, 0] = weapon_hold
        EvnChart.weapon_temp[frame_num, 0] = weapon_temp
        EvnChart.weapon_change[frame_num, 0] = weapon_change
        EvnChart.weapon_change_delayframes[frame_num, 0] = weapon_change_delayframes
        EvnChart.weapon_change_done[frame_num, 0] = weapon_change_done
        EvnChart.damage[frame_num, 0] = damage
        EvnChart.damage_fixed[frame_num, 0] = damage_fixed
        EvnChart.damage_before[frame_num, 0] = damage_before
        EvnChart.damage_ThisRound[frame_num, 0] = damage_ThisRound
        # End Loop
        if weapon_change_done:
            weapon_change_done = False
    txtdata.close()

    EvnDtf = np.zeros([total_frames, 18], dtype=np.object_)
    EvnDtf[:, 0] = EvnChart.frame[:, 0]
    EvnDtf[:, 1] = EvnChart.ammo[:, 0]
    EvnDtf[:, 2] = EvnChart.ammo_before[:, 0]
    EvnDtf[:, 3] = EvnChart.ammo_after[:, 0]
    EvnDtf[:, 4] = EvnChart.shooting[:, 0]
    EvnDtf[:, 5] = EvnChart.shot_pause_flag[:, 0]
    EvnDtf[:, 6] = EvnChart.shot_pause_delayframes[:, 0]
    EvnDtf[:, 7] = EvnChart.weapon[:, 0]
    EvnDtf[:, 8] = EvnChart.weapon_hold[:, 0]
    EvnDtf[:, 9] = EvnChart.weapon_before[:, 0]
    EvnDtf[:, 10] = EvnChart.weapon_temp[:, 0]
    EvnDtf[:, 11] = EvnChart.weapon_change[:, 0]
    EvnDtf[:, 12] = EvnChart.weapon_change_done[:, 0]
    EvnDtf[:, 13] = EvnChart.weapon_change_delayframes[:, 0]
    EvnDtf[:, 14] = EvnChart.damage[:, 0]
    EvnDtf[:, 15] = EvnChart.damage_fixed[:, 0]
    EvnDtf[:, 16] = EvnChart.damage_before[:, 0]
    EvnDtf[:, 17] = EvnChart.damage_ThisRound[:, 0]
    xd = pd.DataFrame(EvnDtf)
    xd.to_excel(
        EvnChartExcel_Path,
        header=[
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
        index=None,
    )

    xdfl = pd.DataFrame(
        Firing_List,
        columns=[
            'Video_Name',
            'Start_Frame',
            'End_Frame',
            'Used_Weapon',
            'Used_Ammo',
            'Damage_Dealt',
        ],
    )
    xdfl.to_excel(FiringList_Path, header=None, index=None)
    if Save_to_BigData:
        bdfl = pd.read_excel(BigDataFL)
        bdfl = bdfl.append(xdfl, ignore_index=True)
        bdfl.to_excel(BigDataFL, index=None)


if __name__ == '__main__':
    vid_path = 'F:/MEDIA/APEX/2023-03-01 21-14-32告别老坛秒吃8KCC.mp4'
    Original_Data = pd.read_excel('./Temp/ReadData_Original.xlsx').values
    FRAMES = Original_Data[:, 0:1]
    WEAPONS = Original_Data[:, 1:2]
    AMMOS = Original_Data[:, 2:3]
    DAMAGES = Original_Data[:, 3:4]
    total_frames = len(FRAMES)
    fps = 60
    Evncht_path = './Temp/EventChart.xlsx'
    Firlst_path = './Temp/Firing_List.xlsx'
    apex_chart_analyze(
        vid_path,
        FRAMES,
        WEAPONS,
        AMMOS,
        DAMAGES,
        total_frames,
        fps,
        Evncht_path,
        Firlst_path,
        True,
    )
