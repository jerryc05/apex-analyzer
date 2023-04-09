from dataclasses import dataclass

from enum import Enum


class WeaponTypes(Enum):
    RIFLE = "r"
    SHORTGUN = "sh"
    PISTOL = "p"
    SNIPER = "sn"
    LIGHT_MACHINE_GUN = "lmg"
    SUBMACHINE_GUN = "smg"
    MARKSMAN = "m"
    SKILL = "skill"


@dataclass
class Weapon:
    name_cn: str  # 名称
    group: WeaponTypes
    is_auto: bool = False  # 全自动
    max_ammo_digits: int = 2  # 最大弹药位数
    bullets_per_shot: int = 1  # Bullets per shot


wp_3030 = Weapon("30-30", WeaponTypes.MARKSMAN, False, 2)
wp_car = Weapon("CAR", WeaponTypes.SUBMACHINE_GUN, True, 2)
wp_eva8 = Weapon("EVA-8", WeaponTypes.SHORTGUN, True, 1)
wp_g7 = Weapon("G7侦查枪", WeaponTypes.MARKSMAN, False, 2)
wp_lstar = Weapon("L-STAR能量机枪", WeaponTypes.LIGHT_MACHINE_GUN, True, 3)
wp_p2020 = Weapon("P2020手枪", WeaponTypes.PISTOL, False, 2)
wp_r99 = Weapon("R-99冲锋枪", WeaponTypes.SUBMACHINE_GUN, True, 2)
wp_r301 = Weapon("R-301卡宾枪", WeaponTypes.RIFLE, True, 2)
wp_mastiff = Weapon("敖犬霰弹枪", WeaponTypes.SHORTGUN, False, 1)
wp_rampage = Weapon("暴走", WeaponTypes.LIGHT_MACHINE_GUN, True, 2)
wp_bocek = Weapon("波塞克", WeaponTypes.MARKSMAN, False, 2)
wp_chargerifle = Weapon("充能步枪", WeaponTypes.SNIPER, False, 1, 2)
wp_volt = Weapon("电能冲锋枪", WeaponTypes.SUBMACHINE_GUN, True, 2)
wp_wingman = Weapon("辅助手枪", WeaponTypes.PISTOL, False, 2)
wp_havoc = Weapon("哈沃克步枪", WeaponTypes.RIFLE, True, 2)
wp_peacekeeper = Weapon("和平捍卫者霰弹枪", WeaponTypes.SHORTGUN, False, 1)
wp_hemlock = Weapon("赫姆洛克突击步枪", WeaponTypes.RIFLE, False, 2)
wp_vantagesniper = Weapon("狙击目标", WeaponTypes.SKILL, False, 1)
wp_kraber = Weapon("克雷贝尔狙击枪", WeaponTypes.SNIPER, False, 1)
wp_prowler = Weapon("猎兽冲锋枪", WeaponTypes.SUBMACHINE_GUN, False, 2)
wp_mozambique = Weapon("莫桑比克", WeaponTypes.SHORTGUN, False, 1)
wp_spitfire = Weapon("喷火轻机枪", WeaponTypes.LIGHT_MACHINE_GUN, True, 2)
wp_flatline = Weapon("平行步枪", WeaponTypes.RIFLE, True, 2)
wp_tripletake = Weapon("三重式狙击枪", WeaponTypes.MARKSMAN, False, 2, 3)
wp_sentinel = Weapon("哨兵狙击步枪", WeaponTypes.SNIPER, False, 1)
wp_longbow = Weapon("长弓", WeaponTypes.SNIPER, False, 2)
wp_devotion = Weapon("专注轻机枪", WeaponTypes.LIGHT_MACHINE_GUN, True, 2)
wp_alternator = Weapon("转换者冲锋枪", WeaponTypes.SUBMACHINE_GUN, True, 2)
wp_sheila = Weapon("转轮机枪", WeaponTypes.SKILL, True, 3)
wp_nemesis = Weapon("复仇女神", WeaponTypes.RIFLE, True, 2)
wp_re45 = Weapon("RE-45自动手枪", WeaponTypes.PISTOL, True, 2)

all_weapons = (
    wp_3030,
    wp_car,
    wp_eva8,
    wp_g7,
    wp_lstar,
    wp_p2020,
    wp_r99,
    wp_r301,
    wp_mastiff,
    wp_rampage,
    wp_bocek,
    wp_chargerifle,
    wp_volt,
    wp_wingman,
    wp_havoc,
    wp_peacekeeper,
    wp_hemlock,
    wp_vantagesniper,
    wp_kraber,
    wp_prowler,
    wp_mozambique,
    wp_spitfire,
    wp_flatline,
    wp_tripletake,
    wp_sentinel,
    wp_longbow,
    wp_devotion,
    wp_alternator,
    wp_sheila,
    wp_nemesis,
    wp_re45,
)

weapon_dict = {x.name_cn: x for x in all_weapons}
