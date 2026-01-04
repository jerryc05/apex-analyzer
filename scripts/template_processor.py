import sys
from pathlib import Path
import cv2
import numpy as np

# 获取项目根目录的绝对路径
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent

# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(project_root))

try:
    from config import TEMPLATE_PROCESSING, ROI_CONFIG, BINARY_THRESHOLD
except ImportError as e:
    print(f"导入配置错误: {e}")
    print(f"请确保在项目根目录({project_root})中存在config.py文件")
    sys.exit(1)
try:
    from utils.image_utils import (
        apply_binary_threshold,
        add_black_background,
        apply_dilation,
    )
except ImportError as e:
    print(f"导入配置错误: {e}")
    print(f"请确保在项目中存在utils/image_utils.py文件")
    sys.exit(1)


def crop_image(image, roi_params):
    """根据ROI参数裁切图像"""
    if image is None:
        raise ValueError("输入图像为空")

    height, width = image.shape[:2]
    x, y, w, h = roi_params

    # 边界检查
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = min(w, width - x)
    h = min(h, height - y)

    # 裁切图像
    cropped = image[y : y + h, x : x + w]

    # 检查裁切结果
    if cropped.size == 0:
        raise ValueError(f"裁切区域无效: 图像尺寸({width}x{height}), ROI({x},{y},{w},{h})")

    return cropped


def process_templates_for_area(area_name):
    """处理指定区域的所有模板"""
    config = TEMPLATE_PROCESSING
    roi_config = ROI_CONFIG.get(area_name)

    if not roi_config:
        print(f"警告: 区域 '{area_name}' 未在ROI配置中定义")
        return 0

    # 获取区域特定路径
    input_dir = config["input_base_dir"] / area_name
    output_dir = config["output_base_dir"] / area_name

    # 确保目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 检查输入目录是否存在
    if not input_dir.exists():
        print(f"错误: 原始模板目录不存在: {input_dir}")
        return 0

    # 获取ROI参数
    target_res = config["target_resolution"]
    roi_params = roi_config.get(target_res)

    # 获取二值化参数

    if not roi_params:
        print(f"错误: 区域 '{area_name}' 缺少 {target_res} 分辨率的ROI配置")
        return 0

    print(f"\n处理区域: {area_name}")
    print(
        f"  ROI参数: x={roi_params[0]}, y={roi_params[1]}, w={roi_params[2]}, h={roi_params[3]}"
    )
    print(f"  输入目录: {input_dir}")
    print(f"  输出目录: {output_dir}")

    processed_count = 0
    image_files = list(input_dir.glob("*.[pP][nN][gG]"))

    if not image_files:
        print(f"警告: 输入目录中没有PNG文件: {input_dir}")
        return 0

    for input_path in image_files:
        # 读取图像（保留alpha通道）
        image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)

        if image is None:
            print(f"警告: 无法读取图像 {input_path.name}")
            continue

        # 检查分辨率
        height, width = image.shape[:2]
        target_w, target_h = config["target_resolution"]

        if (width, height) != (target_w, target_h):
            print(
                f"警告: 图像 {input_path.name} 的分辨率 {width}x{height} "
                f"与目标分辨率 {target_w}x{target_h} 不匹配"
            )

        try:
            # 裁切图像
            cropped = crop_image(image, roi_params)

            # 添加黑色背景
            cropped_bg = add_black_background(cropped)

            # 应用二值化处理
            binary_roi = apply_binary_threshold(cropped_bg, BINARY_THRESHOLD(area_name))

            # 应用膨胀
            dilation = apply_dilation(binary_roi)

            # 保存裁切后的图像
            output_path = output_dir / input_path.name
            cv2.imwrite(str(output_path), dilation)

            print(
                f"  已处理: {input_path.name} -> 保存到 {output_path.relative_to(config['output_base_dir'])}"
            )
            processed_count += 1

        except Exception as e:
            print(f"  处理 {input_path.name} 时出错: {str(e)}")

    return processed_count


def process_all_templates(
    all: bool = True, include_areas: list = [], exclude_areas: list = []
):
    """
    处理所有区域的模板
    :param all: 处理全部模板
    :param include_areas: 需要处理的模板
    :param exclude_areas: (include_areas为空时)需要排除的模板
    """
    config = TEMPLATE_PROCESSING
    print(f"开始模板预处理 (基准分辨率: {config['target_resolution']})")
    print(f"项目根目录: {project_root}")

    total_processed = 0
    for area in config["areas"]:
        if (
            all
            or area in include_areas
            or (len(include_areas) == 0 and not area in exclude_areas)
        ):
            count = process_templates_for_area(area)
            total_processed += count
            print(f"区域 '{area}' 处理完成: {count} 个模板")

    print(f"\n所有区域处理完成! 共处理 {total_processed} 个模板")
    return total_processed


if __name__ == "__main__":
    process_all_templates(all=False, include_areas="ammos")
