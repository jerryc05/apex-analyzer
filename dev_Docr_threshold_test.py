# coding=UTF-8
# 研究二值化阈值对OCR判别准确率的影响
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from damage_ocr import key_capture_test
from tqdm import tqdm


def threshold_test(min_val: int, max_val: int) -> None:
    mat_corrects = np.zeros([max_val - min_val + 1, 1], dtype=np.uint8)
    mat_errs = np.zeros([max_val - min_val + 1, 1], dtype=np.uint8)
    mat_discards = np.zeros([max_val - min_val + 1, 1], dtype=np.uint8)
    mat_tval = np.zeros([max_val - min_val + 1, 1], dtype=np.uint8)
    _p = 0
    with tqdm(total=max_val - min_val + 1) as pbar:
        pbar.update(_p)
        for t_val in range(min_val, max_val + 1):
            corrects, errs, discards = key_capture_test(t_val, False)
            mat_tval[_p, 0] = t_val
            mat_corrects[_p, 0] = corrects
            mat_errs[_p, 0] = errs
            mat_discards[_p, 0] = discards
            _p += 1
            pbar.update(_p - pbar.n)
    dtf = pd.DataFrame(
        np.hstack((mat_tval, mat_corrects, mat_errs, mat_discards)),
        columns=['threshold_val', 'corrects', 'wrongs', 'discards'],
    )
    dtf.to_excel('./Temp/threshold_test.xlsx', index=False)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=300)
    plt.stackplot(
        mat_tval[:, 0],
        np.hstack((mat_corrects, mat_errs, mat_discards)).T,
        baseline='zero',
        labels=['corrects', 'wrongs', 'discards'],
    )
    plt.xlabel('threshold')
    plt.ylabel('images')
    plt.legend()
    fig.savefig('./Temp/threshold_test.png')
    plt.show()


if __name__ == '__main__':
    threshold_test(150, 200)
