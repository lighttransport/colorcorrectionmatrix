#!/usr/bin/env python3

from numpy.random import *
import numpy as np
import csv
import argparse
import math
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

def csvfile2nparray(f):
    str_data = f.read()
    lines = str_data.replace(' ', '').split('\n')
    del lines[len(lines) - 1]

    data = list()
    cells = list()

    for i in range(len(lines)):
        cells.append(lines[i].split(','))

    start_row = 0
    if not cells[0][0].replace(".","",1).isdigit():
        del cells[0]
        start_row = 1

    i = 0
    for line in cells:
        data.append(list())
        for j in range(start_row, len(line)):
            data[i].append(float(line[j]))
        i += 1
    # print(data)

    return np.asarray(data, dtype=np.float32)

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

def drawChartComparison(reference, corrected, matchRatio):
    offset = 15
    patchSize = 100
    patchHalfsize = patchSize / 2
    width = offset + (patchSize + offset) * 6
    height = offset + (patchSize + offset) * 4
    im = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    for i in range(len(reference)):
        ix = i % 6
        iy = int(i / 6)
        rx = offset + (patchSize + offset) * ix
        ry = offset + (patchSize + offset) * iy
        draw.rectangle((rx, ry, rx + patchSize, ry + patchHalfsize),
                       fill=(int(reference[i][0] * 255),
                             int(reference[i][1] * 255),
                             int(reference[i][2] * 255)))
        draw.rectangle((rx, ry + patchHalfsize, rx + patchSize, ry + patchSize),
                       fill=(int(corrected[i][0] * 255),
                             int(corrected[i][1] * 255),
                             int(corrected[i][2] * 255)))
        draw.multiline_text((rx + patchHalfsize - 10, ry + 2 + patchSize),
                            '{0:3.1f}%'.format(matchRatio[i]),
                            fill=(0, 0, 0))
    return im

def saveResultImg(chart, graph, filename):
    offset = 0
    dst = Image.new('RGB', (max(chart.width, graph.width) + offset,
                            chart.height + graph.height + offset),
                    (255, 255, 255))
    dst.paste(chart, (0, 0))
    dst.paste(graph, (0, chart.height + offset))
    dst.save('{}.png'.format(filename))

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
    for rgb in rgbList:
        # (r, g, b)
        xyz = np.dot(M, rgb.transpose())
        xyzList.append(xyz.transpose())
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
    for rgb in rgbList:
        # (r, g, b)
        xyz = np.dot(M, rgb.transpose())
        xyzList.append(xyz.transpose())
    return np.asarray(xyzList)

def correctChart(source, ccm):
    sourceXYZ = sRGB2XYZ(source)
    correctedSource = []

    sourceXYZ = np.append(sourceXYZ, np.ones((24, 1)), axis=1)
    correctedSource = np.dot(sourceXYZ, ccm)

    return XYZ2sRGB(correctedSource)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ccm', action='store',
                        type=argparse.FileType('r'))
    parser.add_argument('referenceCsv', action='store',
                        type=argparse.FileType('r'))
    parser.add_argument('sourceCsv', action='store',
                        type=argparse.FileType('r'))
    parser.add_argument('outputbasename', action='store',
                        type=str)
    # parser.add_argument('-g', '--gamma', type=float, default=1.0, action='store',
    #                     help='Gamma value of reference and source data. (Default=1.0)')
    args = parser.parse_args()
    #gamma = args.gamma

    ccm = loadCCM(args.ccm)
    reference = csvfile2nparray(args.referenceCsv)
    source = csvfile2nparray(args.sourceCsv)

    correctedSource = correctChart(source, ccm)
    diff = np.absolute(np.subtract(reference, correctedSource))
    matchRatio = np.multiply(np.add(np.divide(np.subtract(correctedSource, reference).sum(axis=1),
                                              3),
                                    0),
                             100)
    diffIm = drawChartComparison(reference, correctedSource, matchRatio)

    plt.ylim([-15, 15])
    plt.axes().yaxis.grid(True)
    plt.xlim([-1, 24])
    plt.hlines([0], -1, 25, "red")
    plt.bar(np.arange(len(matchRatio)), matchRatio, align="center", width=0.7)
    plt.vlines([5.5, 11.5, 17.5, 23.5], -20, 20, "red")
    plt.xlabel("Patch")
    plt.ylabel("Match %")
    plt.savefig('graph.png')

    graphIm = Image.open('graph.png', 'r')
    saveResultImg(diffIm, graphIm, args.outputbasename)
