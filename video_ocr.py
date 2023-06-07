import numpy as np
import cv2

# opencv会自动过滤重复帧，故更换
import skvideo.io
import skvideo.datasets
import pandas as pd
from weapon_recognize import weapon_recognize
import weapon_dict
from ammo_ocr import ammo_recognize_cv
from damage_ocr import get_damage


def ms_to_timestr(ms: float):
    time_min = int(ms / 60000)
    time_s = int(ms / 1000) % 60
    return f'{time_min}:{time_s:02}'


def round_report():  # 一梭子汇报
    global shooting, shot_pause_flag, ammo_before, weapon_change_done, damage, damage_fixed, damage_ThisRound, damage_before, Firing_List
    if not weapon_before:
        return None  # 之前没武器
    shot_ammo = ammo_before - ammo_after
    used_weapon = weapon
    if weapon_change_done:
        used_weapon = weapon_before
    # Damage Process
    damage = get_damage(Img, rank_league)
    damage_fixed = max(damage_fixed, damage)
    damage_ThisRound = damage_fixed - damage_before
    damage_before = damage_fixed

    print(
        'frame:{}, time:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
            i, ms_to_timestr(time_ms), used_weapon, shot_ammo, damage_fixed, damage_ThisRound
        )
    )
    print(
        'frame:{}, time:{}, 使用{}打掉{}发弹药, DMG总:{}, DMG本次:{}'.format(
            i, ms_to_timestr(time_ms), used_weapon, shot_ammo, damage_fixed, damage_ThisRound
        ),
        file=txtdata,
    )

    Firing_List.append([firing_start_f, i, used_weapon, shot_ammo, damage_ThisRound])
    shooting = False
    shot_pause_flag = False
    ammo_before = ammo_after


def shot_pause():
    global shot_pause_flag, shot_pause_DelayFrames
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


def temp_frame_save(Img, time, weapon, ammo):
    global tempi
    print(
        'case:{}, frame:{}, time:{}, weapon:{}, ammo:{}'.format(tempi, i, time, weapon, ammo)
    )
    print(
        'case:{}, frame:{}, time:{}, weapon:{}, ammo:{}'.format(tempi, i, time, weapon, ammo),
        file=txtdata,
    )
    cv2.imwrite('./Temp/TempImageSeries/temp' + str(tempi) + '.jpg', Img)
    tempi += 1


def damage_correction(Damage_fixed, Damage_read):  # 修正策略
    if Damage_read - Damage_fixed > 400:
        return Damage_read
    return max(Damage_fixed, Damage_read)


if __name__ == '__main__':
    # vid_path = 'F:/CodeProject/Videos/2023-02-04 11-21-06一打三到偷牌到一起上励志C.mp4'#笔记本
    vid_path = 'F:/MEDIA/APEX/2023-03-01 21-14-32告别老坛秒吃8KCC.mp4'  # 台式机
    rank_league = True
    txtdata = open('Temp/TempLog.txt', 'w', encoding='utf-8')
    print(vid_path, file=txtdata)
    capture = skvideo.io.vreader(vid_path)
    metadata = skvideo.io.ffprobe(vid_path)
    total_frames = int(metadata['video']['@nb_frames'])  # 总帧数
    fps = 60  # 帧率
    # DamageData = np.zeros([int(total_frames), 1], dtype=np.object_)
    i = 0
    tempi = 0
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
    )  # [firing_start_f, firing_end_f, used_weapon, used_ammo, damage_dealt]
    firing_start_f = 0

    class Event_Chart:
        def __init__(self, total_frames: int) -> None:
            self.frame = np.zeros([total_frames, 1], dtype=np.uint32)  # 当前帧
            self.weapon = np.zeros([total_frames, 1], dtype=np.object_)
            self.ammo = np.zeros([total_frames, 1], dtype=np.object_)
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
            self.damage = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage_fixed = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage_before = np.zeros([total_frames, 1], dtype=np.uint16)
            self.damage_ThisRound = np.zeros([total_frames, 1], dtype=np.uint16)

    EvnChart = Event_Chart(total_frames=total_frames)

    if capture is not None:
        for Img in capture:
            time_ms = i * 1000 / fps
            time = ms_to_timestr(time_ms)
            weapon, wpsim = weapon_recognize(Img)
            if weapon:
                if not weapon == weapon_hold:  # 不一样
                    if weapon_change:  # 在变更
                        if weapon == weapon_temp:
                            if (
                                weapon_change_delayframes == Weapon_Change_MaxDelayFrames
                            ):  # 消抖完成
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
                        i += 1
                        continue

                if i % fps == 0:  # 整秒
                    damage = get_damage(Img, rank_league=rank_league)
                    damage_fixed = max(damage_fixed, damage)
                    if not shooting:
                        damage_before = damage_fixed
                ammo_maxdigits = weapon_dict.weapon_dict[weapon].max_ammo_digits
                ammo = ammo_recognize_cv(Img, ammo_maxdigits)
                if not ammo is None:
                    # Sign up: Obtain, Reload, Change

                    if weapon_change_done:  # 换了
                        print('检测到换武器')
                        print('检测到换武器', file=txtdata)
                        # Calculate Last Weapon Damage
                        if shooting:
                            round_report()
                        shooting = False  # 换武器的一刻不可能在射击
                        # Sign up
                        ammo_before = ammo
                        ammo_after = ammo
                        # Data Show
                        temp_frame_save(Img, time, weapon, ammo)
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
                                        firing_start_f = i - 9
                                    shooting = True
                                    shot_pause_flag = False
                            else:  # 可能情况：换枪、换子弹
                                if shooting:
                                    round_report()
                                    temp_frame_save(Img, time, weapon, ammo)
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
                                round_report()
                                temp_frame_save(Img, time, weapon, ammo)
                            ammo_after = ammo
                            ammo_before = ammo
                        else:
                            # 停火计时
                            if shooting:
                                if shot_pause():
                                    print('检测到停火')
                                    print('检测到停火', file=txtdata)
                                    round_report()
                                    temp_frame_save(Img, time, weapon, ammo)

            # Record EventChart
            EvnChart.ammo[i, 0] = ammo
            EvnChart.ammo_after[i, 0] = ammo_after
            EvnChart.ammo_before[i, 0] = ammo_before
            EvnChart.frame[i, 0] = i
            EvnChart.shooting[i, 0] = shooting
            EvnChart.shot_pause_delayframes[i, 0] = shot_pause_DelayFrames
            EvnChart.shot_pause_flag[i, 0] = shot_pause_flag
            EvnChart.weapon[i, 0] = weapon
            EvnChart.weapon_before[i, 0] = weapon_before
            EvnChart.weapon_hold[i, 0] = weapon_hold
            EvnChart.weapon_temp[i, 0] = weapon_temp
            EvnChart.weapon_change[i, 0] = weapon_change
            EvnChart.weapon_change_delayframes[i, 0] = weapon_change_delayframes
            EvnChart.weapon_change_done[i, 0] = weapon_change_done
            EvnChart.damage[i, 0] = damage
            EvnChart.damage_fixed[i, 0] = damage_fixed
            EvnChart.damage_before[i, 0] = damage_before
            EvnChart.damage_ThisRound[i, 0] = damage_ThisRound
            # End Loop
            i += 1
            if weapon_change_done:
                weapon_change_done = False

    else:
        print('视频打开失败')
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
        './Temp/EventChart.xlsx',
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

    xdfl = pd.DataFrame(Firing_List)
    xdfl.to_excel(
        './Temp/Firing_List.xlsx',
        header=['Start_Frame', 'End_Frame', 'Used_Weapon', 'Used_Ammo', 'Damage_Dealt'],
        index=None,
    )
