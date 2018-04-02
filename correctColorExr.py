#!/usr/bin/env python3

import OpenEXR
import Imath
import numpy as np
import csv
import argparse
from PIL import Image

def loadCCM(ccmCsvFile) :
    csvData = ccmCsvFile.read()
    lines = csvData.replace(' ', '').split('\n')
    del lines[len(lines) - 1]

    data = list()
    cells = list()

    for i in range(len(lines)):
        cells.append(lines[i].split(','))

    i = 0
    for line in cells:
        data.append(list())
        for j in range(len(line)):
            data[i].append(float(line[j]))
        i += 1

    return np.asarray(data)

def sRGB2XYZ(rgbList):
    # D 50
    # M = np.array([[0.4360747  0.3850649  0.1430804]
    #                  [0.2225045  0.7168786  0.0606169]
    #                  [0.0139322  0.0971045  0.7141733]])
    # D 65
    M = np.array([[0.412391, 0.357584, 0.180481],
                  [0.212639, 0.715169, 0.072192],
                  [0.019331, 0.119195, 0.950532]])
    xyzList = []
    for l in rgbList:
        xyzSubList = []
        for rgb in l:
            # (r, g, b)
            xyz = np.dot(M, rgb.transpose())
            xyzSubList.append(xyz.transpose())
        xyzList.append(np.asarray(xyzSubList))

    return np.asarray(xyzList)

def XYZ2sRGB(rgbList):
    # D 50
    # M = np.array([[3.1338561 -1.6168667 -0.4906146]
    #                  [-0.9787684  1.9161415  0.0334540]
    #                  [0.0719453 -0.2289914  1.4052427]])
    # D 65
    M = np.array([[3.240970, -1.537383, -0.498611],
                  [-0.969244, 1.875968, 0.041555],
                  [0.055630, -0.203977, 1.056972]])
    xyzList = []
    for l in rgbList:
        xyzSubList = []
        for rgb in l:
            # (r, g, b)
            xyz = np.dot(M, rgb.transpose())
            xyzSubList.append(xyz.transpose())
        xyzList.append(np.asarray(xyzSubList))

    return np.asarray(xyzList)

def correct(rgbList, ccm):
    xyzList = []
    for l in rgbList:
        nl = np.append(l, np.ones((len(l), 1)), axis=1)
        xyzList.append(np.dot(nl, ccm))
    return np.asarray(xyzList)


    # xyzList = []
    # for l in rgbList:
    #     xyzSubList = []
    #     for rgb in l:
    #         rgb1 = np.append(rgb, 1)
    #         xyzSubList.append(np.dot(rgb1, ccm))
    #     xyzList.append(np.asarray(xyzSubList))
    # return np.asarray(xyzList)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ccm', action='store',
                        type=argparse.FileType('r'))
    parser.add_argument('input', action='store')
    parser.add_argument('-o', '--outputBaseName', type=str,
                        default='corrected',action='store')
    parser.add_argument('-g', '--gamma', type=float, default=2.2, action='store',
                        help='Gamma value of reference and source data. (Default=2.2)')
    args = parser.parse_args()

    ccm = loadCCM(args.ccm)
    file = OpenEXR.InputFile(args.input)
    pixelType = Imath.PixelType(Imath.PixelType.FLOAT)
    dw = file.header()['dataWindow']
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1
    rgbStr = file.channels('RGB', pixelType)

    rgb = [np.fromstring(c, dtype=np.float32) for c in rgbStr]
    img = np.vstack(rgb).T.reshape(height, width, 3)

    img = sRGB2XYZ(img)
    img = correct(img, ccm)
    img = XYZ2sRGB(img)

    img = np.clip(img, 0.0, 1.0)

    img = np.power(img, 1. / args.gamma)
    pilImg = Image.fromarray(np.uint8(img * 255.0))
    pilImg.save('{}.png'.format(args.outputBaseName))
