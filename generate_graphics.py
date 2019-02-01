#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import cairosvg

assetdir = 'graphics'
objsdir = 'objs'
dpi = 300

# (clear, dark) colors code for some preset
colors = {'green': ('55ba9a', '459397'),
          'yellow': ('f9dd27', 'f8a423'),
          'blue': ('68a4dd', '5584cc'),
          'brown_light': ('b0ad7f', '908d64'),
          'green_light': ('b1df6e', '84c533'),
          'grey': ('b1c6d0', '7d9fb1'),
          'orange': ('f57c2a', 'f35e21'),
          'purple': ('b568dd', 'b155cc'),
          'cyan': ('68d9dd', '55bdcc'),
          'brown': ('a87e72', '966450'),
          'pink': ('ef87ed', 'e06cea'),
          # 'ocre': ('e6d8a3', 'cbbc7b'),

          'red': ('ef2d32', 'b22922'),
          }

fonts = {'title': os.path.join(assetdir, 'font', 'ZCOOLKuaiLe-Regular.ttf'),
         'credits': os.path.join(assetdir, 'font', 'PT_Sans-Narrow-Web-Regular.ttf'),
         'numbers': os.path.join(assetdir, 'font', 'Graduate-Regular.ttf')}


def generate_color(path, color, color_dict=colors):
    fin = open(path, 'r')
    filename = os.path.splitext(os.path.basename(path))[0]
    out_filename = os.path.join(objsdir, f'{filename}-{color}')
    fout = open(out_filename + '.svg', 'w')
    print(f'[GEN] {filename}, {color}')
    fout.write(fin.read().replace('de7ec7', color_dict[color][0])
                         .replace('bee71e', color_dict[color][1]))
    fout.close()
    cairosvg.svg2png(url=out_filename + '.svg', write_to=out_filename + '.png', dpi=dpi)
    fin.close()


if __name__ == '__main__':
    print(f'[CLEAN] {objsdir}')
    shutil.rmtree(objsdir, ignore_errors=True)
    os.makedirs(objsdir)

    for root, dirs, files in os.walk(os.path.join(assetdir, 'color')):
        for file in files:
            for color in colors.keys():
                generate_color(os.path.join(root, file), color)

    for root, dirs, files in os.walk(os.path.join(assetdir, 'static')):
        for file in files:
            print(f'[GEN] {file}')
            cairosvg.svg2png(url=os.path.join(root, file),
                             write_to=os.path.join(objsdir, file.replace('svg', 'png')),
                             dpi=dpi)
