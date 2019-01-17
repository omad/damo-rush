#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
from mkcard import make_card, make_front_title_card, make_back_title_card
from mkcard import NotPlayableWithRegularGame

from common import load_db


def generate_title_card(icon):
    front = make_front_title_card(icon)
    front.save(os.path.join('generated', f'{icon}-front.png'), 'PNG')
    print(f'[Card] {icon} front generated')
    back = make_back_title_card(icon)
    back.save(os.path.join('generated', f'{icon}-back.png'), 'PNG')
    print(f'[Card] {icon} back generated')


def generate_deck(nb_move, index_move, icon, n, limits):
    assert nb_move <= 60
    shutil.rmtree('generated', ignore_errors=True)
    os.makedirs('generated')

    generate_title_card(icon)

    puzzles = load_db('rush.txt')

    i = [puzzle.nb_move for puzzle in puzzles].index(nb_move) + index_move - 1

    len_n = len(str(n))
    while n:
        if i < len(puzzles):
            puzzle = puzzles[i]
        else:
            raise IndexError('Not enough grid corresponding to the constraint in the database')

        try:
            card = make_card(puzzle, deck=icon, n=n, len_n=len_n, limits=limits)
            n -= 1
        except NotPlayableWithRegularGame:
            i += 1
            continue

        parity = 'odd' if n % 2 else 'even'
        card.save(os.path.join('generated', f'{icon}-{parity}-{n + 1:0{len_n}d}.png'), 'PNG')
        print(f'[Card] {icon} {n + 1} generated ({puzzle.nb_move}, {puzzle.index}/{puzzle.over})')

        i += 1

    print(f'[Info] use {puzzles[i].nb_move, puzzles[i].index} to generate the continuing deck')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a deck of card (decreasingly from starting point')
    parser.add_argument('level', type=int, help='starting level')
    parser.add_argument('index', type=int, help='nth grid for given level')
    parser.add_argument('icon', type=str, help='discriminant icon for the deck')
    parser.add_argument('n', type=int, default=6, nargs='?', help='number of puzzles in the deck')

    parser.add_argument('--minwall', metavar='<n>', type=int, default=0,
                        help='min number of wall (0)')
    parser.add_argument('--maxwall', metavar='<n>', type=int, default=0,
                        help='max number of wall (0)')
    parser.add_argument('--mincar', metavar='<n>', type=int, default=1,
                        help='min number of car (1)')
    parser.add_argument('--maxcar', metavar='<n>', type=int, default=12,
                        help='max number of car (12)')
    parser.add_argument('--mintruck', metavar='<n>', type=int, default=0,
                        help='min number of truck (0)')
    parser.add_argument('--maxtruck', metavar='<n>', type=int, default=4,
                        help='max number of truck (4)')
    args = parser.parse_args()

    args.maxwall = max(args.maxwall, 2)
    args.maxcar = max(args.maxcar, 18)  # Full grid of car
    args.maxtruck = max(args.maxtruck, 11)  # Primary car + full grid of truck

    limits = {1: {'min':args.minwall, 'max':args.maxwall},
              2: {'min':args.mincar, 'max':args.maxcar},
              3: {'min':args.mintruck, 'max':args.maxtruck}}

    print(f'creating deck with constraint: {limits}')
    generate_deck(args.level, args.index, args.icon, args.n, limits)
