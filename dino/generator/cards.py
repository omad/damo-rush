import json
import os.path
from PIL import Image, ImageFont, ImageDraw
from random import shuffle, randrange
import qrcode

from dino.graphics import get_colors


def _img_merge(bg_img, fg_img, coord=(0, 0)):
    # inspire by https://stackoverflow.com/a/53663233
    # merge top left corner of fg_img at coord
    fg_img_trans = Image.new("RGBA", fg_img.size)
    fg_img_trans = Image.blend(fg_img_trans, fg_img, 1)
    bg_img.paste(fg_img_trans, coord, fg_img_trans)


def _make_puzzle_img(elements, unit=100):
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
                (x * unit - c, y * unit - c, x * unit + c, y * unit + c),
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

        _img_merge(car_mask, car, offsets[element]["|"])
        if flip:
            car_mask = car_mask.transpose(Image.FLIP_TOP_BOTTOM)
        if orientation == "-":
            car_mask = car_mask.rotate(90)
        _img_merge(
            grid,
            car_mask,
            (
                unit * x - offsets[element][orientation][0],
                unit * y - offsets[element][orientation][1],
            ),
        )
    return grid


def _get_base_card(rotate=False):
    models = {"bridge": {"bleed": (747, 1122), "safe": (603, 978)}}
    model = "bridge"

    use_template = models[model]
    if rotate:
        for k, v in use_template.items():
            use_template[k] = v[::-1]

    safe_offset = tuple(
        [
            (item1 - item2) // 2
            for item1, item2 in zip(use_template["bleed"], use_template["safe"])
        ]
    )

    return Image.new("RGBA", use_template["bleed"], color='white'), safe_offset


def generate_puzzle_card(puzzle, deck_data=None, unit=100):
    """
    Return a PIL.Image of a puzzle card.
    :param puzzle: A row from the database table of puzzles
    :param deck_data:
    :param unit:
    :return:
    """

    card, safe_offset = _get_base_card()
    puzzle_img = _make_puzzle_img(json.loads(puzzle["elements"]), unit)

    # Center the puzzle on the card
    margex, margey = tuple(
        [(item1 - item2) // 2 for item1, item2 in zip(card.size, puzzle_img.size)]
    )
    _img_merge(card, puzzle_img, (margex, margey))

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
        _img_merge(card, dino, (dx, dy))

        font = ImageFont.truetype(
            os.path.join("graphics", "font", "Graduate-Regular.ttf"), unit // 2
        )
        text = deck_data["text"]
        n_sizex, n_sizey = draw.textsize(text, font=font)
        nx = card.size[0] // 2 + unit // 10
        ny = dy + dino.size[1] // 2 - n_sizey // 2
        draw.text((nx, ny), text, (100, 100, 100), font=font)

    return card


def generate_front_title_card(icon_name):
    card, _ = _get_base_card()
    draw = ImageDraw.Draw(card)
    text = icon_name.capitalize()
    font = ImageFont.truetype(
        os.path.join("graphics", "font", "ZCOOLKuaiLe-Regular.ttf"), 70
    )
    sizex, sizey = draw.textsize(text, font=font)

    dino = Image.open(os.path.join("graphics", "generated", f"big{icon_name}.png"))
    dx = card.size[0] // 2 - dino.size[0] // 2
    dy = card.size[1] // 2 - dino.size[1] // 2 - 3 * sizey
    _img_merge(card, dino, (dx, dy))

    # Add deck name
    x = card.size[0] // 2 - sizex // 2
    y = dy + dino.size[1] + sizey
    draw.text((x, y), text, (150, 150, 150), font=font)

    return card


def generate_back_title_card():
    base_font_size = 18
    # low effort dummy paste of the credits.md file
    card, safe_offset = _get_base_card(rotate=True)

    draw = ImageDraw.Draw(card)
    currentx, currenty = safe_offset

    f = open("credits.md", "r")
    for line in f.readlines():
        text = line.strip()
        if not text:
            currenty += base_font_size // 2
        else:
            fontsize = base_font_size + [0, 8, 6][text.count("#")]
            indent = base_font_size * [2, 0, 1][text.count("#")]
            text = text.strip("# ")
            font = ImageFont.truetype(
                os.path.join("graphics", "font", "PT_Sans-Narrow-Web-Regular.ttf"),
                fontsize,
            )
            sizex, sizey = draw.textsize(text, font=font)
            draw.text((currentx + indent, currenty), text, "grey", font=font)
            currenty += sizey + sizey // 4  # 125% interline

    qr = qrcode.QRCode(box_size=7)
    qr.add_data("https://gitlab.com/crazyiop/dino-rush/")
    qr.make(fit=True)
    qr_img = qr.make_image().convert("RGBA")

    # x position: qr right-align on safe_offset
    qrx = card.size[0] - safe_offset[0] - qr_img.size[0]

    # y position: equalize the margins
    qry = (card.size[1] - qr_img.size[1]) // 2

    _img_merge(card, qr_img, (qrx, qry))

    return card


def _add_number_column(start_x, start_y, n_start, n_end):
    card, (safe_x, safe_y) = _get_base_card()
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(
        os.path.join("graphics", "font", "ZCOOLKuaiLe-Regular.ttf"), 50
    )

    base_x, base_y = draw.textsize("MM", font=font)
    base_size_x = base_x + 2 * base_y
    spacer_x = (card.size[0] - 3 * base_size_x - 2 * safe_x) // 2
    current_x = start_x
    i = n_start
    for col in range(3):
        current_y = start_y
        while current_y + base_y < card.size[1] - safe_y:
            text = f"{i:02}"

            draw.rectangle(
                [current_x, current_y, current_x + base_y, current_y + base_y],
                None,
                (0, 0, 0),
            )

            draw.text(
                (current_x + base_y + base_y // 2, current_y),
                text,
                (0, 0, 0),
                font=font,
            )
            current_y += base_y + base_y // 2
            i += 1
            if i > n_end:
                break
        if i > n_end:
            break
        current_x += spacer_x + base_size_x
    return card, draw, i


def generate_front_score_card(icon_name, n_start=1, n_last=84):
    _, (safe_x, safe_y) = _get_base_card()
    dino = Image.open(os.path.join("graphics", "generated", f"{icon_name}.png"))
    card, draw, n_next = _add_number_column(
        safe_x, safe_y + dino.size[1] + 8, n_start, n_last
    )

    _img_merge(card, dino, (safe_x, safe_y))

    return card, n_next


def generate_back_score_card(icon_name, n_next, n_last=84):
    _, (safe_x, safe_y) = _get_base_card()
    card, draw, _ = _add_number_column(safe_x, safe_y, n_next, n_last)

    return card
