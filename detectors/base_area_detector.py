# coding=UTF-8
import cv2
import numpy as np
from pathlib import Path
import sys
from typing import cast, Dict, Optional, Tuple

# 获取项目根目录的绝对路径
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent

# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(project_root))

try:
    from config import ROI_CONFIG, TEMPLATE_MATCHING, DIGIT_OFFSET
except ImportError as e:
    print(f"导入配置错误: {e}")
    print(f"请确保在项目根目录({project_root})中存在config.py文件")
    sys.exit(1)
try:
    from utils.image_utils import (
        load_binaried_templates,
        get_common_template_size,
    )
except ImportError as e:
    print(f"导入配置错误: {e}")
    print("请确保在项目目录utils中存在image_utils.py文件")
    sys.exit(1)
try:
    from scripts.roi_manager import ROIManager
except ImportError as e:
    print(f"导入配置错误: {e}")
    print("请确保在项目目录scripts中存在roi_manager.py文件")
    sys.exit(1)
# sys.path.remove(str(project_root))


class BaseAreaDetector:
    """模板匹配检测器的基类"""

    def __init__(self, area_name: str, debug: bool = False):
        """
        初始化区域检测器
        :param area_name: 区域名称（如'area1', 'area2'）
        :param debug: 是否启用调试模式
        """
        self.area_name = area_name
        self.debug = debug
        self.roi_manager = ROIManager(ROI_CONFIG)
        self.config = TEMPLATE_MATCHING(area_name)

        # 加载配置参数
        self.binary_threshold = cast(int, self.config["binary_threshold"])
        self.templates = load_binaried_templates(cast(Path, self.config["templates_dir"]))
        self.common_size = get_common_template_size(self.templates)
        self.match_threshold = cast(int, self.config["match_threshold"])
        self.match_method = self.config["method"]

        if not self.templates:
            raise RuntimeError(f"无法加载{area_name}模板，请检查模板目录")

    def process_image(
        self, image: np.ndarray[int, np.dtype[np.uint8]]
    ) -> np.ndarray[int, np.dtype[np.uint8]]:
        """
        处理图像获取标准化的ROI
        :param image: 输入图像
        :return: 处理后的ROI区域
        """
        return self.roi_manager.crop_roi(
            image=image,
            area_name=self.area_name,
            fix_after_first=True,
            binary_threshold=self.binary_threshold,
            scale_to=(self.common_size[1], self.common_size[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    def match_template(
        self,
        roi: np.ndarray[int, np.dtype[np.uint8]],
        template: np.ndarray[int, np.dtype[np.uint8]],
    ) -> float:
        """执行模板匹配"""
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val

    def detect(self, image: np.ndarray[int, np.dtype[np.uint8]]) -> Dict[str, float]:
        """
        检测单张图像
        :param image: 输入图像
        :return: 模板匹配分数字典
        """
        processed_roi = self.process_image(image)
        results = {}
        for name, template in self.templates.items():
            score = self.match_template(processed_roi, template)
            results[name] = score
        return results

    def detect_batch(self, image_paths: list[Path]) -> list[tuple[Path, Dict[str, float]]]:
        """
        批量检测图像
        :param image_paths: 图像路径列表
        :return: 检测结果列表
        """
        results = []
        for path in image_paths:
            image = cv2.imread(str(path))
            if image is None:
                print(f"无法读取图像: {path}")
                continue
            match_results = self.detect(image)
            results.append((path, match_results))
        return results

    def get_best_match(self, results: Dict[str, float]) -> Tuple[Optional[str], float]:
        """获取最佳匹配的模板"""
        best_name, best_score = None, 0
        for name, score in results.items():
            if score > best_score:
                if score > self.match_threshold:
                    best_name = name
                best_score = score
        return best_name, best_score


# 具体区域检测器实现
class WeaponsDetector(BaseAreaDetector):
    """Weapons专用检测器"""

    def __init__(self, debug: bool = False):
        super().__init__("weapons", debug)


class AmmosDetector(BaseAreaDetector):
    """Ammos专用检测器"""

    def __init__(self, debug: bool = False):
        super().__init__("ammos", debug)
        self.digit_offset = DIGIT_OFFSET["ammos"]  # 在roi_manager中处理offset


# 使用示例
if __name__ == "__main__":
    # 初始化检测器
    detector = AmmosDetector(debug=True)
    # 也可以初始化Ammos检测器: AmmosDetector(debug=True)

    # 获取ROI管理器引用
    roi_manager = detector.roi_manager

    # 示例：处理单张图像
    test_image = cv2.imread("./temp/frame_36000.jpg")
    if test_image is not None:
        results = detector.detect(test_image)
        print(results)
        best_name, best_score = detector.get_best_match(results)
        print(f"最佳匹配: {best_name} (分数: {best_score:.4f})")

    # 示例：处理图像序列
    image_dir = Path("screenshots")
    if image_dir.exists():
        image_paths = list(image_dir.glob("*.jpg"))[:10]
        batch_results = detector.detect_batch(image_paths)

        for path, results in batch_results:
            best_name, best_score = detector.get_best_match(results)
            print(f"{path.name}: 最佳匹配 {best_name} (分数: {best_score:.4f})")

    # 获取固定ROI参数
    try:
        roi_params, resolution = roi_manager.get_fixed_roi_params("ammos")
        print(f"固定ROI参数: {roi_params} (分辨率: {resolution})")
    except ValueError as e:
        print(e)
