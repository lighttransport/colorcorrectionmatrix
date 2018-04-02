#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import csv


def load_colorchart_csv(f):
    '''Load color chart data
        Input CSV's shape is (25, 4), which contains one extra row and column.
    '''
    data = np.loadtxt(f, delimiter=",", skiprows=1, usecols=(1, 2, 3))
    assert data.shape == (24, 3)
    return data


def conv_sRGB2XYZ(rgb):
    # D 50
    # M = np.array([[0.4360747  0.3850649  0.1430804]
    #               [0.2225045  0.7168786  0.0606169]
    #               [0.0139322  0.0971045  0.7141733]])
    # D 65
    M = np.array([[0.412391, 0.357584, 0.180481],
                  [0.212639, 0.715169, 0.072192],
                  [0.019331, 0.119195, 0.950532]])
    return np.dot(M, rgb.T).T


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference_csv', type=argparse.FileType('r'))
    parser.add_argument('source_csv', type=argparse.FileType('r'))
    parser.add_argument('output_csv', type=argparse.FileType('w'),
                        default='ccm.csv')
    parser.add_argument('-g', '--gamma', type=float, default=1.0,
                        help='Gamma value of reference and source data.')
    args = parser.parse_args()
    gamma = args.gamma

    # Load color charts
    reference_raw = load_colorchart_csv(args.reference_csv)
    source_raw = load_colorchart_csv(args.source_csv)

    # Degamma
    reference_linear = np.power(reference_raw, gamma)
    source_linear = np.power(source_raw, gamma)

    # XYZ
    reference_xyz = conv_sRGB2XYZ(reference_linear)
    source_xyz = conv_sRGB2XYZ(source_linear)

    # Solve
    # source_xyz * ccm == reference_xyz
    # (24, 3 + 1) * (4, 3) = (24 * 3)
    source_xyz_hm = np.append(source_xyz, np.ones((24, 1)), axis=1)
    ccm = np.linalg.pinv(source_xyz_hm).dot(reference_xyz)

    print('CCM:')
    print(ccm)

    # Write out
    writer = csv.writer(args.output_csv, lineterminator='\n')
    writer.writerows(ccm)
