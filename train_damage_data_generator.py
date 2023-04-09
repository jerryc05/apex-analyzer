import cv2
import numpy as np
import os

sourcefiledir = './Temp/TrainSource/'
destfiledir = './Temp/DmgTrainData/'
DmgRef = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
h, w = np.shape(DmgRef)
p = 0
for source in os.listdir(sourcefiledir):
    Img_source = cv2.imread(sourcefiledir + source, 0)
    # if Rank:
    #     Img_Cut = Img_source[94:120,1675:1761]
    # else:
    #     Img_Cut = Img_source[94:120,1749:1835]#裁剪
    Img_Cut = Img_source[94:120, 1675:1761]
    Img_Cut = cv2.threshold(Img_Cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    H, W = np.shape(Img_Cut)
    sim = np.zeros([W - w, 1])
    for i in range(W - w):
        comp = DmgRef == Img_Cut[:, i : i + w]
        sim[i, 0] = len(np.where(comp == True)[0])
    Logofit = np.where(sim[:, 0] == np.max(sim[:, 0]))[0][0]
    Img_DmgNum = Img_Cut[:, Logofit + w :]
    cv2.imwrite(destfiledir + 'temp_' + str(p) + '.png', Img_DmgNum)
    p += 1
