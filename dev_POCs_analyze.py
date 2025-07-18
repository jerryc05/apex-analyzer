# testing
import cv2
from pathlib import Path
from tqdm import tqdm
import numpy as np
from typing import Tuple, cast
import numpy.typing as npt


def main(vid_path: Path):
    capture = cv2.VideoCapture(str(vid_path))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    read_frames = 36700
    capture.set(cv2.CAP_PROP_POS_FRAMES, 36700)
    with tqdm(total=total_frames) as pbar:
        pbar.update(read_frames)
        while True:
            ret, img_bgr = cast(Tuple[bool, npt.NDArray[np.uint8]], capture.read())
            if not ret and read_frames >= total_frames:
                break
            if not ret and read_frames < total_frames:
                print('error reading frame {}'.format(read_frames))
                capture.set(cv2.CAP_PROP_POS_FRAMES, read_frames + 1)
            read_frames += 1
            pbar.update(read_frames - pbar.n)
    print('frames read:{}/{}'.format(read_frames, total_frames))


if __name__ == '__main__':
    err_path = Path(r'D:\code\videos\2023-05-12 21-38-43弹道6K 变金.mp4')
    main(vid_path=err_path)
