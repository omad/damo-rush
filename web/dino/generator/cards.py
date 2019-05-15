import time
import os.path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


def generate_card(row, deck, current_pos):
    time.sleep(1)
    return None


def generate_puzzle_card(puzzle, deck_data=None):
    print(os.path.abspath("."))
    unit = 100  # dpi of a cell of the puzzle
    models = {"bridge": {"bleed": (747, 1122), "safe": (603, 978)}}
    model = "bridge"

    safe_offset = tuple(
        [
            (item1 - item2) // 2
            for item1, item2 in zip(models[model]["bleed"], models[model]["safe"])
        ]
    )

    card = Image.new("RGBA", models[model]["bleed"])

    puzzle_img = make_puzzle_img(puzzle.get_elements(), unit, limits)

    # Center the puzzle on the card
    margex, margey = tuple(
        [(item1 - item2) // 2 for item1, item2 in zip(card.size, puzzle_img.size)]
    )
    img_merge(card, puzzle_img, (margex, margey))

    # Add puzzle index text
    draw = ImageDraw.Draw(card)
    if puzzle.nb_move and puzzle.index:
        font = ImageFont.truetype(fonts["numbers"], unit)
        text = f"{puzzle.nb_move}"
        lvl_sizex, lvl_sizey = draw.textsize(text, font=font)
        x, y = safe_offset[0] + unit // 5, safe_offset[1] + unit // 5
        draw.text((x, y), text, (0, 0, 0), font=font)

        font = ImageFont.truetype(fonts["numbers"], unit // 2)
        text = " {:,}".format(puzzle.index).replace(",", " ")
        index_sizex, index_sizey = draw.textsize(text, font=font)
        x, y = x + lvl_sizex, y + lvl_sizey - index_sizey
        draw.text((x, y), text, (100, 100, 100), font=font)

        """
        font = ImageFont.truetype(fonts['numbers'], unit // 4)
        text = ' /{:,}'.format(puzzle.over).replace(',', ' ')
        over_sizex, over_sizey = draw.textsize(text, font=font)
        x, y = x + index_sizex, y + index_sizey - over_sizey
        draw.text((x, y), text, (100, 100, 100), font=font)
        """

    # Add icon info if available
    if deck_data:
        dino = Image.open(
            os.path.join("graphics", "generated", f"{deck_data['icon']}.png")
        )
        dx = card.size[0] // 2 - dino.size[0] - unit // 10
        dy = margey + 6 * unit + margey // 2 - dino.size[1] // 2
        img_merge(card, dino, (dx, dy))

        font = ImageFont.truetype(fonts["numbers"], unit // 2)
        font = ImageFont.truetype(
            os.path.join("graphics", "font", "Graduate-Regular.ttf"), unit // 2
        )
        n_sizex, n_sizey = draw.textsize(deck_data["text"], font=font)
        nx = card.size[0] // 2 + unit // 10
        ny = dy + dino.size[1] // 2 - n_sizey // 2
        draw.text((nx, ny), text, (100, 100, 100), font=font)

    return card
