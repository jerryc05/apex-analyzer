# coding=UTF-8
# 读入视频，输出识别未处理数据报表
import argparse
import cv2
import pandas as pd
import pyarrow.feather as feather
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from detectors.weapons_detector import WeaponsDetector


class VideoProcessor:
    def __init__(self, debug=False):
        """
        初始化视频处理器
        :param debug: 是否启用调试模式
        """
        self.debug = debug
        self.detector = WeaponsDetector(debug=debug)
        self.results = []
        self.frame_counter = 0
        self.start_time = None
        self.video_info = {}

        print("视频处理器初始化完成")

    def process_video(self, video_path: str, output_dir: str = "outputs"):
        """
        处理视频文件
        :param video_path: 视频文件路径
        :param output_dir: 输出目录
        """
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成输出文件名
        video_name = Path(video_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{video_name}_{timestamp}"
        feather_path = output_path / f"{base_name}.feather"
        excel_path = output_path / f"{base_name}.xlsx" if self.debug else None

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"错误: 无法打开视频文件 {video_path}")
            return

        # 获取视频信息
        self.video_info = {
            "path": video_path,
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }

        print(
            f"视频信息: {self.video_info['width']}x{self.video_info['height']}, "
            f"{self.video_info['frame_count']}帧, "
            f"{self.video_info['fps']:.2f} FPS"
        )

        # 创建进度条
        pbar = tqdm(total=self.video_info["frame_count"], desc="处理视频帧")

        # 开始处理
        self.start_time = time.time()
        self.frame_counter = 0
        self.results = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 处理当前帧
            frame_result = self.process_frame(frame)

            # 更新进度
            self.frame_counter += 1
            pbar.update(1)

            # 定期更新进度信息
            if self.frame_counter % 100 == 0:
                elapsed = time.time() - self.start_time
                fps = self.frame_counter / elapsed
                eta = (self.video_info["frame_count"] - self.frame_counter) / fps
                pbar.set_postfix({"fps": f"{fps:.1f}", "eta": f"{eta:.1f}s"})

        # 关闭视频
        cap.release()
        pbar.close()

        # 保存结果
        self.save_results(feather_path, excel_path)

        print(
            f"视频处理完成! 处理 {self.frame_counter} 帧, 耗时 {time.time()-self.start_time:.1f} 秒"
        )

    def process_frame(
        self, frame: np.ndarray[int, np.dtype[np.uint8]]
    ) -> dict[str, int | float | str]:
        """
        处理单个视频帧
        :param frame: 视频帧
        :return: 处理结果字典
        """
        frame_time = self.frame_counter / self.video_info["fps"]

        try:
            # 检测当前帧
            match_results = self.detector.detect(frame)
            best_name, best_score = self.detector.get_best_match(match_results)

            # 创建结果记录
            result = {
                "frame": self.frame_counter,
                "timestamp": frame_time,
                "best_match": best_name if best_name else "none",
                # "match_score": best_score if best_name else 0.0,
                "match_score": best_score,
            }

            # 添加所有模板分数
            for name, score in match_results.items():
                result[f"score_{name}"] = score

            # 保存结果
            self.results.append(result)

            # 调试显示
            if self.debug and self.frame_counter % 1000 == 0:
                fig = cv2.putText(
                    frame,
                    f"{best_name}: {best_score:.2f}",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                cv2.imwrite(Path(f"./temp/frame_{self.frame_counter}.jpg"), fig)
            #     cv2.imshow("Video Processing", frame)
            #     if cv2.waitKey(1) & 0xFF == ord('q'):
            #         print("用户中断处理")
            #         return None

            return result

        except Exception as e:
            print(f"处理帧 {self.frame_counter} 时出错: {str(e)}")
            return {
                "frame": self.frame_counter,
                "timestamp": frame_time,
                "best_match": "error",
                "match_score": 0.0,
            }

    def save_results(self, feather_path: Path, excel_path: Path = None):
        """
        保存处理结果
        :param feather_path: Feather 文件路径
        :param excel_path: Excel 文件路径 (可选)
        """
        # 创建 DataFrame
        df = pd.DataFrame(self.results)

        # 添加视频信息
        df["video_path"] = self.video_info["path"]
        df["video_fps"] = self.video_info["fps"]
        df["video_width"] = self.video_info["width"]
        df["video_height"] = self.video_info["height"]

        # 保存为 Feather 格式
        feather.write_feather(df, feather_path)
        print(f"结果已保存为 Feather 格式: {feather_path}")

        # 如果启用调试，保存为 Excel 格式
        if self.debug and excel_path:
            df.to_excel(excel_path, index=False)
            print(f"调试结果已保存为 Excel 格式: {excel_path}")

    def get_performance(self) -> dict[str, int | float]:
        """获取性能统计"""
        if self.frame_counter == 0:
            return {}

        elapsed = time.time() - self.start_time
        fps = self.frame_counter / elapsed

        return {
            "total_frames": self.frame_counter,
            "total_time": elapsed,
            "processing_fps": fps,
            "video_fps": self.video_info["fps"],
        }


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="视频帧识别处理工具")
    parser.add_argument("video", help="输入视频文件路径")
    parser.add_argument("-o", "--output", default="outputs", help="输出目录")
    parser.add_argument("-d", "--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()

    # 检查视频文件是否存在
    if not Path(args.video).exists():
        print(f"错误: 视频文件不存在 {args.video}")
        return

    # 创建并运行处理器
    processor = VideoProcessor(debug=args.debug)
    processor.process_video(args.video, args.output)

    # 打印性能报告
    perf = processor.get_performance()
    print("\n性能报告:")
    print(f"处理帧数: {perf['total_frames']}")
    print(f"总耗时: {perf['total_time']:.1f}秒")
    print(f"处理速度: {perf['processing_fps']:.1f} FPS")
    print(f"视频帧率: {perf['video_fps']:.1f} FPS")
    print(f"实时因子: {perf['processing_fps'] / perf['video_fps']:.2f}x")


if __name__ == "__main__":
    main()
