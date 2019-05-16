import time
import json
import os.path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from random import shuffle, randrange

from dino.graphics import get_colors


def img_merge(bg_img, fg_img, coord=(0, 0)):
    # inspire by https://stackoverflow.com/a/53663233
    fg_img_trans = Image.new("RGBA", fg_img.size)
    fg_img_trans = Image.blend(fg_img_trans, fg_img, 1)
    bg_img.paste(fg_img_trans, coord, fg_img_trans)


def make_puzzle_img(elements, unit=100):
    # Offset from a centered form for each type of element
    offsets = {
        "truck": {"-": (0, unit), "|": (unit, 0)},
        "car": {"-": (unit // 2, unit), "|": (unit, unit // 2)},
        "barrier": {"-": (0, 0), "|": (0, 0)},
    }

    grid = Image.open(os.path.join("graphics", "generated", "grid.png"))
    draw = ImageDraw.Draw(grid)

    c = 3
    for x in range(1, 6):
        for y in range(1, 6):

            draw.ellipse(
                (x * 100 - c, y * 100 - c, x * 100 + c, y * 100 + c),
                fill="grey",
                outline="grey",
            )

    available_colors = []
    colors = get_colors()

    for k, v in elements.items():
        if len(available_colors) == 0:
            # When all colors are used refill the pool
            available_colors = list(colors.keys())
            available_colors.remove("red")  # reserved for primary car
            shuffle(available_colors)

        car_mask = Image.new("RGBA", (3 * unit, 3 * unit))
        if "x" in k:
            element = "barrier"
            subtype = ""
            color = ""
            orientation = "|"
            flip = False
            car = Image.open(os.path.join("graphics", "generated", f"{element}.png"))
        else:
            if k == "A":
                element = "car"
                subtype = "primary"
                color = "red"
                flip = True
            elif len(v) == 3:
                element = "truck"
                subtype = ""
                color = available_colors.pop()
                flip = randrange(2)
            else:
                element = "car"
                subtype = str(randrange(7))
                color = available_colors.pop()
                flip = randrange(2)

            if v[1] - v[0] == 1:
                orientation = "-"
            else:
                orientation = "|"

            car = Image.open(
                os.path.join("graphics", "generated", f"{element}{subtype}-{color}.png")
            )

        y, x = divmod(v[0], 6)

        img_merge(car_mask, car, offsets[element]["|"])
        if flip:
            car_mask = car_mask.transpose(Image.FLIP_TOP_BOTTOM)
        if orientation == "-":
            car_mask = car_mask.rotate(90)
        img_merge(
            grid,
            car_mask,
            (
                unit * x - offsets[element][orientation][0],
                unit * y - offsets[element][orientation][1],
            ),
        )
    return grid


def generate_puzzle_card(puzzle, deck_data=None):
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

    puzzle_img = make_puzzle_img(json.loads(puzzle["elements"]), unit)

    # Center the puzzle on the card
    margex, margey = tuple(
        [(item1 - item2) // 2 for item1, item2 in zip(card.size, puzzle_img.size)]
    )
    img_merge(card, puzzle_img, (margex, margey))

    # Add puzzle index text
    draw = ImageDraw.Draw(card)
    if puzzle["nb_move"] and puzzle["index_"]:
        font = ImageFont.truetype(
            os.path.join("graphics", "font", "Graduate-Regular.ttf"), unit
        )
        text = f"{puzzle['nb_move']}"
        lvl_sizex, lvl_sizey = draw.textsize(text, font=font)
        x, y = safe_offset[0] + unit // 5, safe_offset[1] + unit // 5
        draw.text((x, y), text, (0, 0, 0), font=font)

        font = ImageFont.truetype(
            os.path.join("graphics", "font", "Graduate-Regular.ttf"), unit // 2
        )
        text = " {:,}".format(puzzle["index_"]).replace(",", " ")
        index_sizex, index_sizey = draw.textsize(text, font=font)
        x, y = x + lvl_sizex, y + lvl_sizey - index_sizey
        draw.text((x, y), text, (100, 100, 100), font=font)

    # Add icon info if available
    if deck_data:
        dino = Image.open(
            os.path.join("graphics", "generated", f"{deck_data['icon']}.png")
        )
        dx = card.size[0] // 2 - dino.size[0] - unit // 10
        dy = margey + 6 * unit + margey // 2 - dino.size[1] // 2
        img_merge(card, dino, (dx, dy))

        font = ImageFont.truetype(
            os.path.join("graphics", "font", "Graduate-Regular.ttf"), unit // 2
        )
        n_sizex, n_sizey = draw.textsize(deck_data["text"], font=font)
        nx = card.size[0] // 2 + unit // 10
        ny = dy + dino.size[1] // 2 - n_sizey // 2
        draw.text((nx, ny), text, (100, 100, 100), font=font)

    return card
