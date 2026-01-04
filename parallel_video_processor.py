import argparse
import ctypes
import multiprocessing
from multiprocessing import Pool, Manager, Process, Queue, Value, cpu_count
import signal
import cv2
import numpy as np
import pandas as pd
import pyarrow.feather as feather
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from functools import partial
from detectors.weapons_detector import WeaponsDetector
from config import ROI_CONFIG


class SegmentVideoProcessor:
    def __init__(self, debug=False):
        """
        初始化基于视频分段的并行视频处理器
        :param debug: 是否启用调试模式
        """
        self.debug = debug
        self.video_info = {}
        self.results_queue = None
        self.progress_counter = multiprocessing.Value('i', 0)

        print(f"视频分段处理器初始化完成 (最大进程数: {cpu_count()})")

    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息
        :param video_path: 视频文件路径
        :return: 视频信息字典
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件 {video_path}")

        info = {
            "path": video_path,
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS),
        }

        cap.release()
        return info

    def process_segment(
        self,
        video_path: str,
        start_frame: int,
        end_frame: int,
        segment_id: int,
        progress_counter: Value,
        results_queue: Queue,
    ):
        """
        处理视频片段
        :param video_path: 视频文件路径
        :param start_frame: 起始帧号
        :param end_frame: 结束帧号
        :param segment_id: 片段ID
        :param progress_counter: 进度计数器
        :param results_queue: 结果队列
        """
        try:
            # 每个进程创建独立的检测器
            detector = WeaponsDetector(debug=self.debug)

            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"进程 {segment_id} 错误: 无法打开视频 {video_path}")
                return

            # 跳转到起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # 处理帧
            frame_index = start_frame
            segment_results = []

            while frame_index <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break

                # 计算时间戳
                timestamp = frame_index / self.video_info["fps"]

                # 处理帧
                try:
                    match_results = detector.detect(frame)
                    best_name, best_score = detector.get_best_match(match_results)

                    # 创建结果记录
                    result = {
                        "frame": frame_index,
                        "timestamp": timestamp,
                        "best_match": best_name if best_name else "none",
                        "match_score": best_score,
                    }

                    # 添加所有模板分数
                    for name, score in match_results.items():
                        result[f"score_{name}"] = score

                    segment_results.append(result)

                except Exception as e:
                    print(f"进程 {segment_id} 处理帧 {frame_index} 时出错: {str(e)}")
                    segment_results.append(
                        {
                            "frame": frame_index,
                            "timestamp": timestamp,
                            "best_match": "error",
                            "match_score": 0.0,
                        }
                    )

                # 更新进度
                with progress_counter.get_lock():
                    progress_counter.value += 1

                frame_index += 1

            # 关闭视频
            cap.release()

            # 将结果放入队列
            results_queue.put((segment_id, segment_results))
            results_queue.close()
            print(
                f"进程 {segment_id} 完成: 处理帧 {start_frame}-{end_frame} ({len(segment_results)} 帧)"
            )

        except Exception as e:
            print(f"进程 {segment_id} 发生严重错误: {str(e)}")
        return segment_id, segment_results

    def process_video(
        self,
        video_path: str,
        output_dir: str = "outputs",
        max_processes: int = None,
        segment_seconds: int = 30,
    ):
        """
        处理视频文件
        :param video_path: 视频文件路径
        :param output_dir: 输出目录
        :param max_processes: 最大进程数
        :param segment_seconds: 每个视频片段长度 (秒)
        """
        start_time = time.time()

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成输出文件名
        video_name = Path(video_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{video_name}_{timestamp}"
        feather_path = output_path / f"{base_name}.feather"
        excel_path = output_path / f"{base_name}.xlsx" if self.debug else None

        # 获取视频信息
        self.video_info = self.get_video_info(video_path)
        print(
            f"视频信息: {self.video_info['width']}x{self.video_info['height']}, "
            f"{self.video_info['frame_count']}帧, "
            f"{self.video_info['fps']:.2f} FPS, "
            f"时长: {self.video_info['duration']:.1f}秒"
        )

        # 计算视频片段
        segment_frames = int(segment_seconds * self.video_info["fps"])
        segments = []
        start = 0
        segment_id = 0

        while start < self.video_info["frame_count"]:
            end = min(start + segment_frames - 1, self.video_info["frame_count"] - 1)
            segments.append((start, end, segment_id))
            start = end + 1
            segment_id += 1

        print(f"将视频分成 {len(segments)} 个片段 (每段约 {segment_seconds} 秒)")

        # 创建共享对象
        manager = Manager()
        results_queue = Queue()
        progress_counter = Value(ctypes.c_int, 0)

        # _, segment_results = self.process_segment(
        #     video_path, 0, 1000, 0, progress_counter, results_queue
        # )
        # print(segment_results)
        # while True:
        #     time.sleep(0.5)

        # 确定进程数
        if max_processes is None:
            max_processes = min(cpu_count(), len(segments))
        max_processes = min(max_processes, len(segments))

        print(f"使用 {max_processes} 个进程并行处理")

        # 创建进度条
        pbar = tqdm(total=self.video_info["frame_count"], desc="处理视频帧")

        # 创建并启动进程
        processes = []
        for start, end, seg_id in segments:
            pool = Process(
                target=self.process_segment,
                args=(video_path, start, end, seg_id, progress_counter, results_queue),
            )
            pool.start()
            processes.append(pool)

        # 实时进度监控
        last_count = 0
        completed_processes = 0
        total_processes = len(processes)
        while completed_processes < total_processes:
            # 更新进度条
            with progress_counter.get_lock():
                current_count = progress_counter.value

            if current_count > last_count:
                pbar.update(current_count - last_count)
                last_count = current_count

            # for i, p in enumerate(processes):
            #     if p is not None and not p.is_alive():
            #         completed_processes += 1
            #         processes[i] = None
            #         print(f"进程 {i} 已完成并清除, 总计已结束{i} / {total_processes}")
            # 用Queue长度判断子进程是否已完成任务, 并清除
            len_res_queue = results_queue.qsize()
            if completed_processes < len_res_queue:
                completed_processes = len_res_queue
                print(f"已完成 {completed_processes} / {total_processes} 个进程")

            # 每秒更新一次
            time.sleep(0.1)

        # 确保最后更新完成
        print("确保进度更新完成")
        remaining = self.video_info['frame_count'] - last_count
        if remaining > 0:
            pbar.update(remaining)

        # 关闭进度条
        pbar.close()

        # 收集所有结果
        all_results = []
        while not results_queue.empty():
            print(f"results_queue剩余量:{results_queue.qsize()}")
            seg_id, segment_results = results_queue.get()
            all_results.extend(segment_results)

        # 等待所有进程完成
        for i, pool in enumerate(processes):
            if pool is not None:
                print(f"等待进程 {i} 结束...")
                pool.join()

        # 按帧号排序
        all_results.sort(key=lambda x: x["frame"])

        # 添加视频信息
        for result in all_results:
            result["video_path"] = self.video_info["path"]
            result["video_fps"] = self.video_info["fps"]
            result["video_width"] = self.video_info["width"]
            result["video_height"] = self.video_info["height"]

        # 保存结果
        self.save_results(all_results, feather_path, excel_path)

        # 性能报告
        processing_time = time.time() - start_time
        fps = self.video_info["frame_count"] / processing_time
        print(
            f"视频处理完成! 处理 {self.video_info['frame_count']} 帧, 耗时 {processing_time:.1f} 秒"
        )
        print(f"处理速度: {fps:.1f} FPS")
        print(f"实时因子: {fps / self.video_info['fps']:.2f}x")

    def save_results(self, results: list, feather_path: Path, excel_path: Path = None):
        """
        保存处理结果
        :param results: 结果列表
        :param feather_path: Feather 文件路径
        :param excel_path: Excel 文件路径 (可选)
        """
        # 创建 DataFrame
        df = pd.DataFrame(results)

        # 保存为 Feather 格式
        feather.write_feather(df, feather_path)
        print(f"结果已保存为 Feather 格式: {feather_path}")

        # 如果启用调试，保存为 Excel 格式
        if self.debug and excel_path:
            df.to_excel(excel_path, index=False)
            print(f"调试结果已保存为 Excel 格式: {excel_path}")

    def process_frame_debug(
        self, frame: np.ndarray, frame_index: int, timestamp: float
    ) -> dict:
        """
        调试模式下的帧处理 (带可视化)
        """
        # 创建独立的检测器
        detector = WeaponsDetector(debug=True)

        try:
            # 检测当前帧
            match_results = detector.detect(frame)
            best_name, best_score = detector.get_best_match(match_results)

            # 创建结果记录
            result = {
                "frame": frame_index,
                "timestamp": timestamp,
                "best_match": best_name if best_name else "none",
                "match_score": best_score,
            }

            # 添加所有模板分数
            for name, score in match_results.items():
                result[f"score_{name}"] = score

            # 可视化
            if best_name and frame % 1000 == 0:
                fig = cv2.putText(
                    frame,
                    f"{best_name}: {best_score:.2f}",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                cv2.imwrite(Path(f"./temp/frame_{frame}.jpg"), fig)
            return result

        except Exception as e:
            print(f"处理帧 {frame_index} 时出错: {str(e)}")
            return {
                "frame": frame_index,
                "timestamp": timestamp,
                "best_match": "error",
                "match_score": 0.0,
            }


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="基于视频分段的并行视频处理工具")
    parser.add_argument("video", help="输入视频文件路径")
    parser.add_argument("-o", "--output", default="outputs", help="输出目录")
    parser.add_argument("-d", "--debug", action="store_true", help="启用调试模式")
    parser.add_argument(
        "-p", "--processes", type=int, default=None, help="最大进程数 (默认: CPU核心数)"
    )
    parser.add_argument(
        "-s", "--segment", type=int, default=30, help="视频片段长度 (秒, 默认: 30)"
    )
    args = parser.parse_args()

    # 检查视频文件是否存在
    if not Path(args.video).exists():
        print(f"错误: 视频文件不存在 {args.video}")
        return

    # 创建并运行处理器
    processor = SegmentVideoProcessor(debug=args.debug)

    processor.process_video(
        args.video, args.output, max_processes=args.processes, segment_seconds=args.segment
    )


if __name__ == "__main__":
    # 设置多进程启动方法为 spawn
    if multiprocessing.get_start_method(allow_none=True) != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
    # 修复 Windows 下的多进程问题
    multiprocessing.freeze_support()
    # 忽略 SIGINT 信号，让子进程处理自己的中断
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        main()
    finally:
        # 恢复原始信号处理程序
        signal.signal(signal.SIGINT, original_sigint_handler)
