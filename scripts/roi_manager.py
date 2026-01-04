import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import sys

# 获取项目根目录的绝对路径
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent

# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(project_root))
try:
    from utils.image_utils import (
        apply_binary_threshold,
        apply_dilation,
        scale_image,
    )
except ImportError as e:
    print(f"导入配置错误: {e}")
    print(f"请确保在项目中存在utils/image_utils.py文件")
    sys.exit(1)


class ROIManager:
    def __init__(
        self, roi_config: Dict[str, Dict[Tuple[int, int], Tuple[int, int, int, int]]]
    ):
        """
        初始化 ROI 管理器

        :param roi_config: ROI 配置字典
            格式: {
                "area_name": {
                    (width, height): (x, y, w, h),
                    ...
                }
            }
        """
        self.roi_config = roi_config
        self.fixed_roi_params: Dict[str, Tuple[int, int, int, int]] = {}
        self.fixed_resolutions: Dict[str, Tuple[int, int]] = {}

        # 缓存
        self.roi_cache: Dict[str, Dict[Tuple[int, int], np.ndarray]] = {}

        # print(f"ROI 管理器初始化完成，支持 {len(roi_config)} 个区域")

    def get_roi_params(
        self,
        image: np.ndarray[int, np.dtype[np.uint8]],
        area_name: str,
        fix_after_first: bool = True,
    ) -> Tuple[Tuple[int, int, int, int], Tuple[int, int]]:
        """
        获取指定区域的 ROI 参数

        :param image: 输入图像
        :param area_name: 区域名称
        :param fix_after_first: 是否在第一次确定后固定 ROI
        :return: (x, y, w, h), (width, height) 分辨率
        """
        # 检查是否已固定
        if area_name in self.fixed_roi_params and fix_after_first:
            return self.fixed_roi_params[area_name], self.fixed_resolutions[area_name]

        # 获取图像分辨率
        height, width = image.shape[:2]
        resolution = (width, height)

        # 获取区域配置
        area_config = self.roi_config.get(area_name)
        if not area_config:
            raise ValueError(f"区域 '{area_name}' 未在配置中定义")

        # 查找精确匹配的分辨率
        if resolution in area_config:
            roi_params = area_config[resolution]
        else:
            # 查找最接近的分辨率
            closest_res = min(
                area_config.keys(), key=lambda r: abs(r[0] - width) + abs(r[1] - height)
            )
            roi_params = area_config[closest_res]
            print(f"警告: 区域 '{area_name}' 使用最接近的分辨率 {closest_res} 的配置")

        # 如果设置了固定，则保存参数
        if fix_after_first:
            self.fixed_roi_params[area_name] = roi_params
            self.fixed_resolutions[area_name] = resolution
            # print(f"固定区域 '{area_name}' 的 ROI 参数: {roi_params}")

        return roi_params, resolution

    def crop_roi(
        self,
        image: np.ndarray[int, np.dtype[np.uint8]],
        area_name: str,
        fix_after_first: bool = True,
        binary_threshold: Optional[int] = None,
        scale_to: Optional[Tuple[int, int]] = None,
        interpolation: int = cv2.INTER_LINEAR,
    ) -> np.ndarray[int, np.dtype[np.uint8]]:
        """
        裁切并处理指定区域的 ROI

        :param image: 输入图像
        :param area_name: 区域名称
        :param fix_after_first: 是否在第一次确定后固定 ROI
        :param binary_threshold: 二值化阈值 (None 表示不处理)
        :param scale_to: 缩放目标尺寸 (width, height) (None 表示不缩放)
        :param interpolation: 缩放插值方法
        :return: 处理后的 ROI 图像
        """
        # # 生成缓存键
        # cache_key = (area_name, tuple(image.shape[:2]), binary_threshold, scale_to)

        # # 检查缓存
        # if cache_key in self.roi_cache.get(area_name, {}):
        #     return self.roi_cache[area_name][cache_key].copy()

        # 获取 ROI 参数
        roi_params, _ = self.get_roi_params(image, area_name, fix_after_first)
        x, y, w, h = roi_params

        # 裁切 ROI
        roi = image[y : y + h, x : x + w]

        # 应用二值化
        if binary_threshold is not None:
            roi = apply_binary_threshold(roi, binary_threshold)
            roi = apply_dilation(roi)

        # 应用缩放
        if scale_to:
            target_width, target_height = scale_to
            roi = scale_image(roi, target_width, target_height, interpolation)

        # # 更新缓存
        # if area_name not in self.roi_cache:
        #     self.roi_cache[area_name] = {}
        # self.roi_cache[area_name][cache_key] = roi.copy()

        return roi

    def get_fixed_roi_params(
        self, area_name: str
    ) -> Tuple[Tuple[int, int, int, int], Tuple[int, int]]:
        """
        获取已固定的 ROI 参数

        :param area_name: 区域名称
        :return: (x, y, w, h), (width, height) 分辨率
        """
        if area_name not in self.fixed_roi_params:
            raise ValueError(f"区域 '{area_name}' 尚未固定 ROI 参数")
        return self.fixed_roi_params[area_name], self.fixed_resolutions[area_name]

    def clear_cache(self):
        """清除所有缓存"""
        self.roi_cache = {}
        print("ROI 缓存已清除")

    def clear_fixed_roi(self, area_name: str = None):
        """
        清除固定 ROI

        :param area_name: 区域名称 (None 表示清除所有)
        """
        if area_name:
            if area_name in self.fixed_roi_params:
                del self.fixed_roi_params[area_name]
                del self.fixed_resolutions[area_name]
                print(f"区域 '{area_name}' 的固定 ROI 已清除")
        else:
            self.fixed_roi_params = {}
            self.fixed_resolutions = {}
            print("所有固定 ROI 已清除")
