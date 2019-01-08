#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
from mkcard import make_card, make_front_title_card, make_back_title_card
from mkcard import NotPlayableWithRegularGame


def index_from_id(nb_move_search, index_move_search):
    current_index = 0
    current_move = 0
    f = open('rush.txt', 'r')
    for i, line in enumerate(f.readlines()):
        nb_move, data, nb_state = line.split()
        nb_move = int(nb_move)
        if nb_move != current_move:
            current_index = 1
            current_move = nb_move
            if current_move < nb_move_search:
                raise ValueError(f'Cannot find {nb_move_search}, {index_move_search}')
        else:
            current_index += 1
        if nb_move == nb_move_search and current_index == index_move_search:
            return i + 1
    raise ValueError(f'Cannot find {nb_move_search}, {index_move_search}')


def generate_title_card(icon):
    front = make_front_title_card(icon)
    front.save(os.path.join('generated', f'{icon}-front.png'), 'PNG')
    print(f'[Card] {icon} front generated')
    back = make_back_title_card(icon)
    back.save(os.path.join('generated', f'{icon}-back.png'), 'PNG')
    print(f'[Card] {icon} back generated')


def generate_deck(nb_move, index_move, icon, n):
    assert nb_move <= 60
    shutil.rmtree('generated', ignore_errors=True)
    os.makedirs('generated')

    generate_title_card(icon)

    f = open('rush.txt', 'r')
    start_index = index_from_id(nb_move, index_move)
    for _ in range(start_index - 1):
        f.readline()

    len_n = len(str(n))
    while n:
        line = f.readline()
        try:
            card = make_card(line, deck=icon, n=n, len_n=len_n)
            n -= 1
        except NotPlayableWithRegularGame:
            print(f'WARNING: {line} is not playable with a regular game, skipping it...')
            continue

        parity = 'odd' if n % 2 else 'even'
        card.save(os.path.join('generated', f'{icon}-{parity}-{n + 1:0{len_n}d}.png'), 'PNG')
        print(f'[Card] {icon} {n + 1} generated')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a deck of card')
    parser.add_argument('level', type=int)
    parser.add_argument('index', type=int)
    parser.add_argument('icon', type=str)
    parser.add_argument('n', type=int, default=6, nargs='?')
    args = parser.parse_args()
    generate_deck(args.level, args.index, args.icon, args.n)
