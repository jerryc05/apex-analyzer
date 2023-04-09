# coding=UTF-8
from video_ocr_read_opencv import read_apex_video
from chart_analyze import apex_chart_analyze
from datetime import datetime


def full_analyze_apex_video(
    Video_path,
    Output_EvnChart_Path=None,
    Output_Firlst_Path=None,
    Output_Original_Path=None,
    rank_league=True,
):
    FRAMES, WEAPONS, AMMOS, DAMAGES, total_frames, fps = read_apex_video(
        Video_Path=Video_path, Output_Excel_Path=Output_Original_Path, rank_league=rank_league
    )
    apex_chart_analyze(
        Video_Path=Video_path,
        FRAMES=FRAMES,
        WEAPONS=WEAPONS,
        AMMOS=AMMOS,
        DAMAGES=DAMAGES,
        total_frames=total_frames,
        fps=fps,
        EvnChartExcel_Path=Output_EvnChart_Path,
        FiringList_Path=Output_Firlst_Path,
        Save_to_BigData=True,
    )


if __name__ == '__main__':
    Vidpath = 'F:/MEDIA/APEX/2023-03-30 21-15-31艾许决赛圈2V6 8KCC.mp4'
    Evncht_path = './Temp/EventChart.xlsx'
    Firlst_path = './Temp/Firing_List.xlsx'
    Original_path = './Temp/ReadData_Original.xlsx'
    tic = datetime.now()
    full_analyze_apex_video(
        Vidpath,
        Output_Firlst_Path=Firlst_path,
        Output_EvnChart_Path=Evncht_path,
        Output_Original_Path=Original_path,
    )
    toc = datetime.now()
    print('Elapsed time: %f seconds' % (toc - tic).total_seconds())
