import cv2
import numpy as np
from pathlib import Path


def get_roi_for_resolution(image, roi_config):
    """
    根据图像分辨率获取对应的ROI区域
    :param image: 输入图像 (numpy数组)
    :param roi_config: ROI配置字典 {(width, height): (x, y, w, h)}
    :return: 裁切后的ROI区域
    """
    height, width = image.shape[:2]

    # 查找精确匹配的分辨率
    for res, roi_params in roi_config.items():
        if res[0] == width and res[1] == height:
            x, y, w, h = roi_params
            return image[y : y + h, x : x + w]

    # 如果没有精确匹配，使用最接近的分辨率
    closest_res = min(roi_config.keys(), key=lambda r: abs(r[0] - width) + abs(r[1] - height))
    print(
        f"警告: 未找到精确匹配的分辨率 {width}x{height}, 使用最接近的 {closest_res[0]}x{closest_res[1]} 配置"
    )
    x, y, w, h = roi_config[closest_res]
    return image[y : y + h, x : x + w]


def apply_binary_threshold(image, threshold_value=225):
    """
    应用二值化阈值处理
    :param image: 输入图像 (灰度或BGR)
    :param threshold_value: 阈值 (0-255)
    :return: 二值化后的图像
    """
    if len(image.shape) == 3:
        # 如果是彩色图像，转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 应用二值化阈值 (THRESH_BINARY_INV)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)
    return binary


def apply_dilation(
    image: np.ndarray[int, np.dtype[np.uint8]], kernel_value: int = 3
) -> np.ndarray[int, np.dtype[np.uint8]]:  # 膨胀
    """
    应用膨胀处理
    :param image: 输入图像(灰度或BGR)
    :param kernel_value: 膨胀系数
    """
    if len(image.shape) == 3:
        # 如果是彩色图像，转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    kernel = np.ones((kernel_value, kernel_value), np.uint8)
    dilation = cv2.dilate(gray, kernel, iterations=1)
    return dilation


def load_binary_templates(
    templates_dir, threshold_value=225
) -> dict[str, np.ndarray[int, np.dtype[np.uint8]]]:
    """
    加载并二值化指定目录中的所有模板
    :param templates_dir: 模板目录路径
    :param threshold_value: 二值化阈值
    :return: 二值化模板字典 {模板名称: 二值化图像}
    """
    templates = {}
    for file_path in Path(templates_dir).glob("*.png"):
        # 读取模板图像（保留alpha通道）
        template = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if template is None:
            print(f"警告: 无法读取模板 {file_path.name}")
            continue

        # 处理alpha通道
        if template.shape[2] == 4:  # 带alpha通道
            # 创建白色背景
            background = np.ones_like(template[:, :, :3]) * 255
            # 提取前景
            alpha = template[:, :, 3] / 255.0
            # 合成图像
            template_bgr = (
                background * (1 - alpha[:, :, np.newaxis])
                + template[:, :, :3] * alpha[:, :, np.newaxis]
            )
            template_bgr = template_bgr.astype(np.uint8)
        else:  # 不带alpha通道
            template_bgr = template

        # 应用二值化
        binary_template = apply_binary_threshold(template_bgr, threshold_value)

        templates[file_path.stem] = binary_template

    if not templates:
        print(f"错误: 在 {templates_dir} 中没有找到有效模板")

    return templates


def load_binaried_templates(
    templates_dir: Path,
) -> dict[str, np.ndarray[int, np.dtype[np.uint8]]]:
    """
    加载已经二值化的指定目录中的所有模板
    :param templates_dir: 模板目录路径
    :return: 二值化模板字典 {模板名称: 二值化图像}
    """
    templates = {}
    for file_path in Path(templates_dir).glob("*.png"):
        # 读取模板图像（保留alpha通道）
        template = cv2.imread(str(file_path))
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        if template is None:
            print(f"警告: 无法读取模板 {file_path.name}")
            continue
        templates[file_path.stem] = template

    if not templates:
        print(f"错误: 在 {templates_dir} 中没有找到有效模板")

    return templates


def add_black_background(img):
    """
    使用OpenCV将透明区域替换为黑色背景
    :param input_path: 输入PNG文件路径
    :param output_path: 输出PNG文件路径
    """
    if img.shape[2] == 4:  # 确保有Alpha通道
        # 分离通道：B, G, R, Alpha
        b, g, r, alpha = cv2.split(img)

        # 将Alpha通道归一化到[0, 1]范围
        alpha_normalized = alpha.astype(float) / 255.0

        # 将RGB通道与Alpha相乘（透明区域变为0）
        b = (b * alpha_normalized).astype(np.uint8)
        g = (g * alpha_normalized).astype(np.uint8)
        r = (r * alpha_normalized).astype(np.uint8)

        # 合并通道并移除Alpha
        result = cv2.merge([b, g, r])
    else:
        result = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 无透明通道则直接转换

    return result


def scale_image(
    image: np.ndarray,
    target_width: int,
    target_height: int,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    """
    缩放图像到指定尺寸

    :param image: 输入图像
    :param target_width: 目标宽度
    :param target_height: 目标高度
    :param interpolation: 插值方法
    :return: 缩放后的图像
    """
    # 检查是否需要缩放
    if image.shape[1] == target_width and image.shape[0] == target_height:
        return image.copy()

    return cv2.resize(image, (target_width, target_height), interpolation=interpolation)


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """
    裁切图像指定区域

    :param image: 输入图像
    :param x: 起始X坐标
    :param y: 起始Y坐标
    :param width: 裁切宽度
    :param height: 裁切高度
    :return: 裁切后的图像
    """
    # 边界检查
    h, w = image.shape[:2]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    width = min(width, w - x)
    height = min(height, h - y)

    return image[y : y + height, x : x + width]


def get_common_template_size(
    templates: dict[str, np.ndarray[int, np.dtype[np.uint8]]],
) -> tuple[int, int]:
    """获取模板的公共尺寸"""
    if not templates:
        return (0, 0)

    sizes = set(tpl.shape for tpl in templates.values())
    if len(sizes) == 1:
        return sizes.pop()

    # 返回最常见的尺寸
    size_counter = {}
    for tpl in templates.values():
        size = tpl.shape
        size_counter[size] = size_counter.get(size, 0) + 1

    return max(size_counter, key=size_counter.get)
