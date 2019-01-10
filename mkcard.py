#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os.path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from collections import defaultdict
from random import shuffle, randrange, choice
import qrcode

from generate_graphics import colors, objsdir, fonts


class NotPlayableWithRegularGame(Exception):
    pass


# Card size for printing in dpi
models = {'bridge': {'bleed': (747, 1122), 'safe': (603, 978)}}


def img_merge(bg_img, fg_img, coord=(0, 0)):
    # inspire by https://stackoverflow.com/a/53663233
    fg_img_trans = Image.new("RGBA", fg_img.size)
    fg_img_trans = Image.blend(fg_img_trans, fg_img, 1)
    bg_img.paste(fg_img_trans, coord, fg_img_trans)


def find_id(grid=None, n=None):
    # Return an info dict of the grid given
    current_move = 0
    current_index = 0
    index_for_moves = 0
    f = open('rush.txt', 'r')
    found = False
    for i, line in enumerate(f.readlines()):
        nb_move, data, nb_state = line.split()
        if nb_move != current_move:
            if found:
                return {'moves': int(current_move),
                        'index': int(index_for_moves),
                        'over_total': int(current_index),
                        'states': int(nb_state)}
            current_move = nb_move
            current_index = 1
        else:
            current_index += 1
        if grid == data or n == (i - 1):
            found = True
            index_for_moves = current_index
    raise ValueError('grid not in the database')


def parse_data(database_line):
    parts = database_line.split()
    if len(parts) == 1:
        data = database_line
    elif len(parts) == 3:
        _, data, _ = database_line.split()
    else:
        raise ValueError('Wrong input format', parts)

    puzzle_info = find_id(data)
    if puzzle_info['index'] == puzzle_info['over_total']:
        puzzle_info['index_eol'] = '¬'
    else:
        puzzle_info['index_eol'] = ''

    elements = defaultdict(list)
    nb_wall = 0
    for i, c in enumerate(data):
        if c != 'o':
            if c == 'x':
                nb_wall += 1
                c = 'x' + str(nb_wall)
            elements[c].append(i)
    return elements, puzzle_info


def make_puzzle_img(elements, unit=100):
    # Offset from a centered form for each type of element
    offsets = {'truck': {'-': (0, unit), '|': (unit, 0)},
               'car': {'-': (unit // 2, unit), '|': (unit, unit // 2)},
               'barrier': {'-': (0, 0), '|': (0, 0)}}

    grid = Image.open(os.path.join(objsdir, 'grid.png'))
    draw = ImageDraw.Draw(grid)

    c = 3
    for x in range(1, 6):
        for y in range(1, 6):

            draw.ellipse((x * 100 - c, y * 100 - c, x * 100 + c, y * 100 + c),
                         fill = 'grey', outline ='grey')

    available_colors = []

    nb_car = len([k for k, v in elements.items() if len(v) == 2])
    nb_truck = len([k for k, v in elements.items() if len(v) == 3])

    if nb_car > 12 or nb_truck > 4:  # Walls are easy to diy and would cut too much puzzles
        raise NotPlayableWithRegularGame

    for k, v in elements.items():
        if len(available_colors) == 0:
            # When all colors are used refill the pool
            available_colors = list(colors.keys())
            available_colors.remove('red')  # reserved for primary car
            shuffle(available_colors)

        car_mask = Image.new("RGBA", (3 * unit, 3 * unit))
        if 'x' in k:
            element = 'barrier'
            subtype = ''
            color = ''
            orientation = '|'
            flip = False
            car = Image.open(os.path.join(objsdir, element + '.png'))
        else:
            if k == 'A':
                element = 'car'
                subtype = 'primary'
                color = 'red'
                flip = True
            elif len(v) == 3:
                element = 'truck'
                subtype = ''
                color = available_colors.pop()
                flip = randrange(2)
            else:
                element = 'car'
                subtype = str(randrange(7))
                color = available_colors.pop()
                flip = randrange(2)

            if v[1] - v[0] == 1:
                orientation = '-'
            else:
                orientation = '|'

            car = Image.open(os.path.join(objsdir, element + subtype + '-' + color + '.png'))

        y, x = divmod(v[0], 6)
        # print(k, element, orientation, x, y, color)

        img_merge(car_mask, car, offsets[element]['|'])
        if flip:
            car_mask = car_mask.transpose(Image.FLIP_TOP_BOTTOM)
        if orientation == '-':
            car_mask = car_mask.rotate(90)
        img_merge(grid, car_mask, (unit * x - offsets[element][orientation][0],
                                   unit * y - offsets[element][orientation][1]))
    return grid


def make_front_title_card(deck, model='bridge'):
    card = Image.new("RGBA", models[model]['bleed'])
    draw = ImageDraw.Draw(card)
    text = deck.capitalize()
    font = ImageFont.truetype(fonts['title'], 70)
    sizex, sizey = draw.textsize(text, font=font)

    dino = Image.open(os.path.join(objsdir, f'{deck}-big.png'))
    dx = card.size[0] // 2 - dino.size[0] // 2
    dy = card.size[1] // 2 - dino.size[1] // 2 - 3 * sizey
    img_merge(card, dino, (dx, dy))

    # Add deck name
    x = card.size[0] // 2 - sizex // 2
    y = dy + dino.size[1] + sizey
    draw.text((x, y), text, (150, 150, 150), font=font)

    return card


def make_back_title_card(deck, model='bridge'):
    base_font_size = 18
    # low effort dummy paste of the credits.md file
    card = Image.new("RGBA", models[model]['bleed'][::-1])
    safe_offset = tuple([(item1 - item2) // 2 for item1, item2
                         in zip(models[model]['bleed'], models[model]['safe'])])

    draw = ImageDraw.Draw(card)
    currentx, currenty = safe_offset

    f = open('credits.md', 'r')
    for line in f.readlines():
        text = line.strip()
        if not text:
            currenty += base_font_size
        else:
            fontsize = base_font_size + [0, 8, 6][text.count('#')]
            indent = base_font_size * [2, 0, 1][text.count('#')]
            text = text.strip('# ')
            font = ImageFont.truetype(fonts['credits'], fontsize)
            sizex, sizey = draw.textsize(text, font=font)
            draw.text((currentx + indent, currenty), text, 'grey', font=font)
            currenty += sizey + sizey // 4

    qr = qrcode.QRCode(box_size=7)
    qr.add_data('https://gitlab.com/crazyiop/dino-rush/blob/master/credits.md')
    qr.make(fit=True)
    qr_img = qr.make_image().convert("RGBA")

    qrx = card.size[0] - safe_offset[0] - qr_img.size[0]
    qry = card.size[1] // 2 - qr_img.size[1] // 2
    img_merge(card, qr_img, (qrx, qry))
    return card


def make_card(database_line, model='bridge', deck=None, n=None, len_n=3):
    unit = 100  # dpi of a cell of the puzzle

    safe_offset = tuple([(item1 - item2) // 2 for item1, item2
                         in zip(models[model]['bleed'], models[model]['safe'])])

    card = Image.new("RGBA", models[model]['bleed'])

    elements, info = parse_data(database_line)
    puzzle_img = make_puzzle_img(elements, unit)

    # Center the puzzle on the card
    margex, margey = tuple([(item1 - item2) // 2 for item1, item2
                            in zip(card.size, puzzle_img.size)])
    img_merge(card, puzzle_img, (margex, margey))

    # Add puzzle index text
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(fonts['numbers'], unit)
    text = f"{info['moves']:0{len_n}d}"
    lvl_sizex, lvl_sizey = draw.textsize(text, font=font)
    x, y = safe_offset[0] + unit // 5, safe_offset[1] + unit // 5
    draw.text((x, y), text, (0, 0, 0), font=font)

    font = ImageFont.truetype(fonts['numbers'], unit // 2)
    text = ' {:,}'.format(info['index']).replace(',', ' ') + info['index_eol']
    index_sizex, index_sizey = draw.textsize(text, font=font)
    x, y = x + lvl_sizex, y + lvl_sizey - index_sizey
    draw.text((x, y), text, (100, 100, 100), font=font)

    # Add deck info if available
    if (deck is not None and n is not None):
        dino = Image.open(os.path.join(objsdir, f'{deck}.png'))
        dx = card.size[0] // 2 - dino.size[0] - unit // 10
        dy = margey + 6 * unit + margey // 2 - dino.size[1] // 2
        img_merge(card, dino, (dx, dy))

        font = ImageFont.truetype(fonts['numbers'], unit // 2)
        text = f'{n:0{len_n}d}'
        n_sizex, n_sizey = draw.textsize(text, font=font)
        nx = card.size[0] // 2 + unit // 10
        ny = dy + dino.size[1] // 2 - n_sizey // 2
        draw.text((nx, ny), text, (100, 100, 100), font=font)

    return card


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a card for a rush hour problem')
    parser.add_argument('line', help='string represented a grid, or a line from the database',
                        type=str,
                        nargs='?',
                        default=None)
    parser.add_argument('--level', metavar='<n>', type=int)
    parser.add_argument('--save', action='store_true', help='Save a card instead of showing it')
    args = parser.parse_args()
    if args.line:
        make_card(args.line).show()
    else:
        while True:
            f = open('rush.txt', 'r')
            lines = f.readlines()
            if args.level:
                lines = [line for line in lines if line.split()[0] == str(args.level)]
            line = choice(lines)
            try:
                if args.save:
                    make_card(line).save('standalone.png')
                else:
                    make_card(line).show()
                break
            except NotPlayableWithRegularGame:
                print('Grid generated not playable, chosing another one')
                pass
