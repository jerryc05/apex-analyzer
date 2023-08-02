from pathlib import Path
import sys
from typing import Any, List


def sys_input() -> List[str | int]:
    sys_inputs = []
    video_info = []
    if len(sys.argv) > 1:
        for _p in range(len(sys.argv)):
            if _p:
                _str = sys.argv[_p]
                if Path(_str).is_file():
                    if len(video_info):
                        assert len(video_info) == 1 or len(video_info) == 3, 'wrong inputs!'
                        sys_inputs.append(video_info)
                    video_info = [Path(_str)]
                else:
                    if len(video_info):
                        video_info.append(int(_str))
        if len(video_info):
            assert len(video_info) == 1 or len(video_info) == 3, 'wrong inputs!'
            sys_inputs.append(video_info)
    return sys_inputs


def csv_input() -> List[str | int]:
    csv_inputs = []
    assert Path('./input_videos.txt').is_file(), "input_videos.txt not found or is not a file!"
    input_txt = open('./input_videos.txt', encoding='utf-8')
    for _line in input_txt:
        video_str = _line.strip()
        video_info = video_str.split(',')
        for _p in range(len(video_info)):
            video_info[_p] = video_info[_p].strip()
            if _p:
                video_info[_p] = int(video_info[_p])
        video_info[0] = Path(video_info[0])
        assert video_info[
            0
        ].is_file(), f"video_path [{video_info[0]}] not found or is not a file!"
        assert len(video_info) == 1 or len(video_info) == 3, 'wrong inputs!'
        csv_inputs.append(video_info)
    return csv_inputs


def input_videos() -> List[Any]:
    list_inputs = sys_input()
    if len(list_inputs) == 0:
        list_inputs = csv_input()
    return list_inputs


if __name__ == '__main__':
    print(input_videos())
