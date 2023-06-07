import cv2
import numpy as np
import os

sourcefiledir = './Temp/TrainSource/'
destfiledir = './Temp/DmgTrainData/'
IMG_DMGREF = cv2.imread('./Ref/DmgLogo/DmgLogo.png', 0)
h, w = np.shape(IMG_DMGREF)
p = 0
for source in os.listdir(sourcefiledir):
    Img_source = cv2.imread(sourcefiledir + source, 0)
    # if Rank:
    #     Img_Cut = Img_source[94:120,1675:1761]
    # else:
    #     Img_Cut = Img_source[94:120,1749:1835]#裁剪
    img_cut = Img_source[94:120, 1675:1761]
    img_cut = cv2.threshold(img_cut, 190, 255, cv2.THRESH_BINARY_INV)[1]  # 二值化
    H, W = np.shape(img_cut)
    sim = np.zeros([W - w, 1])
    for i in range(W - w):
        comp = IMG_DMGREF == img_cut[:, i : i + w]
        sim[i, 0] = len(np.where(comp == True)[0])
    logofit = np.where(sim[:, 0] == np.max(sim[:, 0]))[0][0]
    img_dmgnum = img_cut[:, logofit + w :]
    cv2.imwrite(destfiledir + 'temp_' + str(p) + '.png', img_dmgnum)
    p += 1
