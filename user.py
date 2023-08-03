# coding=UTF-8
from datetime import datetime
from pathlib import Path
from typing import Tuple
import numpy as np

from tqdm import tqdm

from chart_analyze import apex_chart_analyze
from video_ocr_read_opencv import read_apex_video, get_total_frames
from func_input_videos import input_videos
import multiprocessing as mp


def full_analyze_apex_video(
    video_path: Path,
    output_evnchart_path: Path,
    output_fl_path: Path,
    output_original_path: Path,
    rank_league: bool | None = None,
    start_frame: int | None = None,
    end_frame: int | None = None,
):
    Path('./Temp').mkdir(parents=True, exist_ok=True)
    Path('./BigData').mkdir(parents=True, exist_ok=True)
    Path('./Output').mkdir(parents=True, exist_ok=True)
    FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps = read_apex_video(
        video_path=video_path,
        output_original_data=output_original_path,
        start_frame=start_frame,
        end_frame=end_frame,
    )
    apex_chart_analyze(
        video_path=video_path,
        FRAMES=FRAMES,
        WEAPONS=WEAPONS,
        AMMOS=AMMOS,
        DAMAGES=DAMAGES,
        TOTAL_FRAMES=total_frames,
        FPS=fps,
        eventchart_path=output_evnchart_path,
        fl_path=output_fl_path,
        saveto_bigdata=True,
    )


def split_reader(
    video_path: Path,
    output_original_path: Path,
    start_frame: int | None = None,
    end_frame: int | None = None,
    process_id: int = 0,
) -> Tuple[
    int,
    np.ndarray[int, np.dtype[np.uint16]],
    np.ndarray[int, np.dtype[np.object_]],
    np.ndarray[int, np.dtype[np.object_]],
    np.ndarray[int, np.dtype[np.uint16]],
    int,
    int,
]:
    FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps = read_apex_video(
        video_path=video_path,
        output_original_data=output_original_path,
        start_frame=start_frame,
        end_frame=end_frame,
        process_id=process_id,
    )
    return (process_id, FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps)


def multi_reader():
    pass  # 想好了再写zddsr


def single_process_reader():
    video_paths = input_videos()
    evnchart_path = Path('./Temp/event_chart.feather')
    fl_path = Path('./Temp/firing_list.feather')
    original_data_path = Path('./Temp/readdata_original.feather')
    for video_info in video_paths:
        video_path = video_info[0]
        start_frame = None
        end_frame = None
        if len(video_info) == 3:
            start_frame = video_info[1]
            end_frame = video_info[2]
        print(video_path)

        tic = datetime.now()
        full_analyze_apex_video(
            video_path,
            output_fl_path=fl_path,
            output_evnchart_path=evnchart_path,
            output_original_path=original_data_path,
            start_frame=start_frame,
            end_frame=end_frame,
        )

        toc = datetime.now()
        print(f'Elapsed time: {(toc - tic).total_seconds()} seconds')


def multi_process_reader() -> None:
    mp.freeze_support()
    video_paths = input_videos()
    evnchart_path = Path('./Temp/event_chart.feather')
    fl_path = Path('./Temp/firing_list.feather')
    original_data_path = Path('./Temp/readdata_original.feather')
    for video_info in video_paths:
        video_path = video_info[0]
        start_frame = None
        end_frame = None
        if len(video_info) == 3:
            start_frame = video_info[1]
            end_frame = video_info[2]
        print(video_path)
        if start_frame is None:
            start_frame = 0
            end_frame = get_total_frames(video_path=video_path)
        proc_count = mp.cpu_count()  # 皮一下，压榨所有CPU
        frames_per_process = int((end_frame - start_frame) / proc_count)
        proc_start_frame = start_frame
        proc_kwds = []
        for proc_id in range(proc_count):
            proc_end_frame = proc_start_frame + frames_per_process
            if proc_id == proc_count - 1:
                proc_end_frame = end_frame
            proc_kwds.append(
                {
                    'video_path': video_path,
                    'output_original_path': original_data_path,
                    'start_frame': proc_start_frame,
                    'end_frame': proc_end_frame,
                    'process_id': proc_id,
                }
            )
            proc_start_frame = proc_end_frame
        mp_results = []
        results = []
        tic = datetime.now()
        with mp.Pool(proc_count, initializer=tqdm.set_lock, initargs=(mp.RLock(),)) as p:
            for idx in range(proc_count):
                print(f'starting process{idx}')
                mp_results.append(p.apply_async(split_reader, kwds=proc_kwds[idx]))
            p.close()
            p.join()
        print('All subprocesses done!')
        for res in mp_results:
            results.append(res.get())
        res_args = [x[0] for x in results]
        res_argsorted = np.argsort(np.array(res_args))
        mat_frames = results[res_argsorted[0]][1]
        mat_weapons = results[res_argsorted[0]][2]
        mat_ammos = results[res_argsorted[0]][3]
        mat_damages = results[res_argsorted[0]][4]
        total_frames = results[res_argsorted[0]][5]
        fps = results[res_argsorted[0]][6]
        for i in range(1, len(results)):
            mat_frames = np.vstack((mat_frames, results[res_argsorted[i]][1]))
            mat_weapons = np.vstack((mat_weapons, results[res_argsorted[i]][2]))
            mat_ammos = np.vstack((mat_ammos, results[res_argsorted[i]][3]))
            mat_damages = np.vstack((mat_damages, results[res_argsorted[i]][4]))
            total_frames += results[res_argsorted[i]][5]
        # 根据res[0]定顺序，vstack所有返回值
        toc = datetime.now()
        print(f'Elapsed time: {(toc - tic).total_seconds()} seconds')
        apex_chart_analyze(
            video_path=video_path,
            FRAMES=mat_frames,
            WEAPONS=mat_weapons,
            AMMOS=mat_ammos,
            DAMAGES=mat_damages,
            TOTAL_FRAMES=total_frames,
            FPS=fps,
            eventchart_path=evnchart_path,
            fl_path=fl_path,
            saveto_bigdata=True,
        )


if __name__ == '__main__':
    multi_process_reader()
