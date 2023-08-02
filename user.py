# coding=UTF-8
from datetime import datetime
from pathlib import Path

from chart_analyze import apex_chart_analyze
from video_ocr_read_opencv import read_apex_video
from func_input_videos import input_videos
import multiprocessing


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


def main():
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


if __name__ == '__main__':
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
        frames_count = multiprocessing.Value('d', 0)

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
