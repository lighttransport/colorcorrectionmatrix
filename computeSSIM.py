#!/usr/bin/env python3

from numpy.random import *
import numpy as np
import csv
import argparse
import math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference', action='store')
    parser.add_argument('corrected', action='store')
    parser.add_argument('-o', '--outputBaseName', action='store',
                        default='ssim')
    args = parser.parse_args()

    resizeFactor = 1.

    corrected_img = Image.open(args.corrected, 'r').convert("L")
    reference_img = Image.open(args.reference, 'r').convert("L")
    reference_img.thumbnail((corrected_img.width * resizeFactor,
                             corrected_img.height * resizeFactor),
                            Image.LANCZOS)
    print('reference {} x {}'.format(reference_img.width, reference_img.height))
    print('corrected {} x {}'.format(corrected_img.width, corrected_img.height))

    print('Computing MSE/PSNR......')
    diffIm = ImageChops.difference(reference_img, corrected_img)
    diff_px = diffIm.getdata()
    mse = 0
    for i in range(len(diff_px)):
        mse += diff_px[i] * diff_px[i]
    mse = mse / len(diff_px)

    l_max = 255
    psnr = 20 * math.log10(l_max) - 10 * math.log10(mse)
    print('MSE: {}\nPSNR: {}'.format(mse, psnr))

    print('Computing SSIM......')
    window_width = 2
    window_size = (window_width * 2 + 1) * (window_width * 2 + 1)
    ref_px = reference_img.getdata()
    corrected_px = corrected_img.getdata()
    mw = min(reference_img.width, corrected_img.width)
    mh = min(reference_img.height, corrected_img.height)

    c1 = math.pow(0.01 * 255, 2)
    c2 = math.pow(0.03 * 255, 2)
    ssim_sum = 0
    ssim_img = Image.new('RGB', ((mw - 2 * window_width),
                                 (mh - 2 * window_width)))
    data = []
    for y in range(window_width, mh - window_width):
        for x in range(window_width, mw - window_width):
            avg_corrected_sum = 0
            avg_reference_sum = 0
            # Compute Average
            for dx in range(-window_width, window_width + 1):
                for dy in range(-window_width, window_width + 1):
                    avg_corrected_sum += corrected_img.getpixel((x + dx, y + dy))
                    avg_reference_sum += reference_img.getpixel((x + dx, y + dy))
            avg_corrected = avg_corrected_sum / window_size
            avg_reference = avg_reference_sum / window_size

            dev_corrected_sum = 0
            dev_reference_sum = 0
            cov_sum = 0
            # Compute Standard Deviation and Covariance
            for dx in range(-window_width, window_width + 1):
                for dy in range(-window_width, window_width + 1):
                    dev_ref = reference_img.getpixel((x + dx, y + dy)) - avg_reference
                    dev_cor = corrected_img.getpixel((x + dx, y + dy)) - avg_corrected
                    dev_reference_sum += dev_ref * dev_ref
                    dev_corrected_sum += dev_cor * dev_cor
                    cov_sum += dev_ref * dev_cor
            dev_corrected = math.sqrt(dev_corrected_sum / window_size)
            dev_reference = math.sqrt(dev_reference_sum / window_size)
            covariance = cov_sum / window_size

            ssim_window = ((2 * avg_corrected * avg_reference + c1) * (2 * covariance + c2)) / \
                          ((avg_corrected * avg_corrected + avg_reference * avg_reference + c1) * \
                           (dev_corrected * dev_corrected + dev_reference * dev_reference + c2))
            ssim_sum += ssim_window
            data.append((int((1.0 - ssim_window) * 255.0),
                         0,
                         int(ssim_window * 255.0)))
    ssim_img.putdata(data)
    ssim_img.save('{}.png'.format(args.outputBaseName))
    ssim = ssim_sum / ((mw - 2 * window_width) * (mh - 2 * window_width))
    print('Average SSIM: {}'.format(ssim))
