from pathlib import Path
import sys


def input_videos() -> list():
    video_paths = []
    if len(sys.argv) > 1:
        for _p in range(len(sys.argv)):
            if _p:
                video_path = Path(sys.argv[_p])
                assert (
                    video_path.is_file()
                ), f"video_path [{video_path}] not found or is not a file!"
                video_paths.append(video_path)
    else:
        assert Path(
            './input_videos.txt'
        ).is_file(), "input_videos.txt not found or is not a file!"
        input_txt = open('./input_videos.txt', encoding='utf-8')
        for _line in input_txt:
            video_path = Path(_line.strip())
            assert (
                video_path.is_file()
            ), f"video_path [{video_path}] not found or is not a file!"
            video_paths.append(video_path)
    video_paths = []
    if len(sys.argv) > 1:
        for _p in range(len(sys.argv)):
            if _p:
                video_path = Path(sys.argv[_p])
                assert (
                    video_path.is_file()
                ), f"video_path [{video_path}] not found or is not a file!"
                video_paths.append(video_path)
    else:
        assert Path(
            './input_videos.txt'
        ).is_file(), "input_videos.txt not found or is not a file!"
        input_txt = open('./input_videos.txt', encoding='utf-8')
        for _line in input_txt:
            video_path = Path(_line.strip())
            assert (
                video_path.is_file()
            ), f"video_path [{video_path}] not found or is not a file!"
            video_paths.append(video_path)
    return video_paths
