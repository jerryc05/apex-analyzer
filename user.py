# coding=UTF-8
from datetime import datetime
from pathlib import Path

from chart_analyze import apex_chart_analyze
from video_ocr_read_opencv import read_apex_video

import sys


def full_analyze_apex_video(
    video_path: Path,
    output_evnchart_path: Path,
    output_fl_path: Path,
    output_original_path: Path,
    rank_league: bool | None = None,
):
    Path('./Temp').mkdir(parents=True, exist_ok=True)
    Path('./BigData').mkdir(parents=True, exist_ok=True)
    Path('./Output').mkdir(parents=True, exist_ok=True)
    FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps = read_apex_video(
        video_path=video_path,
        output_original_data=output_original_path,
        rank_league=rank_league,
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
    #video_path =  Path("# Your APEX Video")
    assert len(sys.argv) > 1, 'Provide a path to the video file!'
    video_path = Path(sys.argv[1])
    assert video_path.is_file(), f"video_path [{video_path}] not found or is not a file!"

    evnchart_path = Path('./Temp/event_chart.feather')
    fl_path = Path('./Temp/firing_list.feather')
    original_data_path = Path('./Temp/readdata_original.feather')
    tic = datetime.now()
    full_analyze_apex_video(
        video_path,
        output_fl_path=fl_path,
        output_evnchart_path=evnchart_path,
        output_original_path=original_data_path,
    )

    toc = datetime.now()
    print(f'Elapsed time: {(toc - tic).total_seconds()} seconds')


if __name__ == '__main__':
    main()
