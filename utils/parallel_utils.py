import os
import math
import concurrent.futures
from typing import List, Tuple, Callable, Any
from tqdm import tqdm


def parallel_process(
    items: list,
    process_func: Callable[[Any], Any],
    *,
    max_workers: int = None,
    chunk_size: int = 10,
    desc: str = "Processing",
    use_tqdm: bool = True,
) -> List[Any]:
    """
    并行处理项目列表

    :param items: 要处理的项目列表
    :param process_func: 处理函数，接受一个项目作为输入
    :param max_workers: 最大工作线程数
    :param chunk_size: 每个任务块的大小
    :param desc: 进度条描述
    :param use_tqdm: 是否使用进度条
    :return: 处理结果列表
    """
    # 确定工作线程数
    if max_workers is None:
        max_workers = os.cpu_count() or 4

    # 计算任务块
    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    # 处理单个任务块
    def process_chunk(chunk: list) -> list:
        return [process_func(item) for item in chunk]

    # 并行处理所有任务块
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(process_chunk, chunk): i for i, chunk in enumerate(chunks)}

        # 准备进度条
        if use_tqdm:
            pbar = tqdm(total=len(chunks), desc=desc)

        # 按完成顺序收集结果
        for future in concurrent.futures.as_completed(futures):
            chunk_index = futures[future]
            try:
                chunk_result = future.result()
                results.append((chunk_index, chunk_result))
            except Exception as e:
                print(f"处理块 {chunk_index} 时出错: {str(e)}")
                results.append((chunk_index, []))

            if use_tqdm:
                pbar.update(1)

        if use_tqdm:
            pbar.close()

    # 按原始顺序重组结果
    sorted_results = sorted(results, key=lambda x: x[0])
    final_results = []
    for _, chunk_result in sorted_results:
        final_results.extend(chunk_result)

    return final_results


def calculate_optimal_chunk_size(total_items: int, max_workers: int) -> int:
    """
    计算最佳任务块大小

    :param total_items: 总项目数
    :param max_workers: 最大工作线程数
    :return: 最佳任务块大小
    """
    # 每个工作线程处理至少100个项目
    min_chunks = max_workers * 10
    chunk_size = max(1, total_items // min_chunks)

    # 限制最大块大小
    max_chunk_size = 100
    return min(chunk_size, max_chunk_size)
