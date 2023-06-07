# coding=UTF-8
from video_ocr_read_opencv import read_apex_video
from chart_analyze import apex_chart_analyze
from datetime import datetime


def full_analyze_apex_video(
    video_path: str,
    output_evnchart_path: str = None,
    output_fl_path: str = None,
    output_original_path: str = None,
    rank_league: bool = None,
):
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


if __name__ == '__main__':
    video_path = '# Your APEX Video'
    evnchart_path = './Temp/event_chart.feather'
    fl_path = './Temp/firing_list.feather'
    original_data_path = './Temp/readdata_original.feather'
    tic = datetime.now()
    full_analyze_apex_video(
        video_path,
        output_fl_path=fl_path,
        output_evnchart_path=evnchart_path,
        output_original_path=original_data_path,
    )

    toc = datetime.now()
    print('Elapsed time: %f seconds' % (toc - tic).total_seconds())
