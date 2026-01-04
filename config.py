from pathlib import Path
import cv2

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# 基准分辨率
BASE_RESOLUTION = (2560, 1440)

# 不同区域、不同分辨率的ROI配置
# 格式: 区域名: {分辨率: (x, y, w, h)}
ROI_CONFIG = {
    "weapons": {
        (2560, 1440): (2055, 1277, 207, 51),
        (1920, 1080): (1541, 958, 155, 38),
    },
    "ammos": {  # 个位数
        (2560, 1440): (2343, 1286, 29, 40),
        (1920, 1080): (1757, 964, 22, 30),
    },
}

# 数字类位数偏移像素
DIGIT_OFFSET = {
    "ammos": {
        (2560, 1440): -35,
        (1920, 1080): -26,
    },
}

# 二值化阈值
BINARY_THRESHOLD_DATABASE = {
    "default": {
        "template": 150,
        "use": 150,
    },
    "weapons": {
        "template": 150,
        "use": 150,
    },
    "ammos": {
        "template": 210,
        "use": 210,
    },
}


# 模板处理配置
TEMPLATE_PROCESSING = {
    "input_base_dir": PROJECT_ROOT / "assets" / "templates_raw",
    "output_base_dir": PROJECT_ROOT / "ui",
    "target_resolution": BASE_RESOLUTION,
    "areas": list(ROI_CONFIG.keys()),  # 支持多区域处理
}

# 模板匹配配置
TEMPLATE_MATCHING_DATABASE = {
    "weapons": {
        "templates_dir": PROJECT_ROOT / "ui" / "weapons",
        "match_threshold": 0.60,  # 匹配阈值 (0-1)
        "method": cv2.TM_CCOEFF_NORMED,  # 匹配方法
        "binary_threshold": BINARY_THRESHOLD_DATABASE["weapons"]["use"],  # 二值化阈值
        "scale_to_template": True,
        "interpolation": cv2.INTER_NEAREST,  # 二值图使用最近邻插值更快
    },
    "ammos": {
        "templates_dir": PROJECT_ROOT / "ui" / "ammos",
        "match_threshold": 0.60,  # 匹配阈值 (0-1)
        "method": cv2.TM_CCOEFF_NORMED,  # 匹配方法
        "binary_threshold": BINARY_THRESHOLD_DATABASE["ammos"]["use"],  # 二值化阈值
        "scale_to_template": True,
        "interpolation": cv2.INTER_NEAREST,  # 二值图使用最近邻插值更快
    },
    "default": {
        "templates_dir": PROJECT_ROOT / "ui" / "weapons",
        "match_threshold": 0.60,  # 匹配阈值 (0-1)
        "method": cv2.TM_CCOEFF_NORMED,  # 匹配方法
        "binary_threshold": BINARY_THRESHOLD_DATABASE["default"]["use"],  # 二值化阈值
        "scale_to_template": True,
        "interpolation": cv2.INTER_NEAREST,  # 二值图使用最近邻插值更快
    },
}


# 模板匹配提取
def TEMPLATE_MATCHING(key: str = 'default') -> dict:
    try:
        return TEMPLATE_MATCHING_DATABASE[key]
    except KeyError:
        return TEMPLATE_MATCHING_DATABASE["default"]


# 二值化匹配提取
def BINARY_THRESHOLD(key1: str = "default", key2: str = "template") -> int:
    """
    获取二值化阈值
    :param key1:一级分支(模板名)
    :param key2:二级分支(template或use)
    """
    try:
        return BINARY_THRESHOLD_DATABASE[key1][key2]
    except KeyError:
        try:
            return BINARY_THRESHOLD_DATABASE[key1]["template"]
        except KeyError:
            return BINARY_THRESHOLD_DATABASE["default"]["template"]
