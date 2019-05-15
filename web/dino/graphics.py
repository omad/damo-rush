from collections import Counter, defaultdict
import json
import os
import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


import os
import shutil
import cairosvg
from .svg_resize import process_stream as svg_resize


def generate_car_color(in_path, out_path, color_name, color_value, dpi):
    fin = open(in_path, "r")
    filename = os.path.splitext(os.path.basename(in_path))[0]
    out_filename = os.path.join(out_path, f"{filename}-{color_name}")
    fout = open(out_filename + ".svg", "w")
    fout.write(
        fin.read().replace("de7ec7", color_value[0]).replace("bee71e", color_value[1])
    )
    fout.close()
    cairosvg.svg2png(url=out_filename + ".svg", write_to=out_filename + ".png", dpi=dpi)
    fin.close()


def generate_icon_size(root, file, out_path, size, dpi, prefix=""):
    filename = f"{prefix}{file}"
    svg_resize(
        {
            "input": os.path.join(root, file),
            "output": os.path.join("/", "tmp", filename),
            "width": f"{size}px",
            "height": f"{size}px",
        }
    )
    cairosvg.svg2png(
        url=os.path.join("/", "tmp", filename),
        write_to=os.path.join(out_path, filename.replace("svg", "png")),
        dpi=dpi,
    )


def mk_graphics(assetdir, objsdir, dpi):
    # (clear, dark) colors code for some preset
    colors = {
        "green": ("55ba9a", "459397"),
        "yellow": ("f9dd27", "f8a423"),
        "blue": ("68a4dd", "5584cc"),
        "brown_light": ("b0ad7f", "908d64"),
        "green_light": ("b1df6e", "84c533"),
        "grey": ("b1c6d0", "7d9fb1"),
        "orange": ("f57c2a", "f35e21"),
        "purple": ("b568dd", "b155cc"),
        "cyan": ("68d9dd", "55bdcc"),
        "brown": ("a87e72", "966450"),
        "pink": ("ef87ed", "e06cea"),
        # 'ocre': ('e6d8a3', 'cbbc7b'),
        "red": ("ef2d32", "b22922"),
    }

    fonts = {
        "title": os.path.join(assetdir, "font", "ZCOOLKuaiLe-Regular.ttf"),
        "credits": os.path.join(assetdir, "font", "PT_Sans-Narrow-Web-Regular.ttf"),
        "numbers": os.path.join(assetdir, "font", "Graduate-Regular.ttf"),
    }

    print(f"[CLEAN] {objsdir}")
    shutil.rmtree(objsdir, ignore_errors=True)
    os.makedirs(objsdir)

    for root, dirs, files in os.walk(os.path.join(assetdir, "color")):
        for file in files:
            for color_name, color_value in colors.items():
                print(f'[GEN] {file.replace("svg", "png")}, {color_name}')
                generate_car_color(
                    os.path.join(root, file), objsdir, color_name, color_value, dpi
                )

    for root, dirs, files in os.walk(os.path.join(assetdir, "static")):
        for file in files:
            if root.endswith("dino"):
                print(f'[GEN] {file.replace("svg", "png")}')
                generate_icon_size(root, file, objsdir, dpi, 100)
                print(f'[GEN] big{file.replace("svg", "png")}')
                generate_icon_size(root, file, objsdir, dpi, 600, prefix="big")
            else:
                print(f'[GEN] {file.replace("svg", "png")}')
                cairosvg.svg2png(
                    url=os.path.join(root, file),
                    write_to=os.path.join(objsdir, file.replace("svg", "png")),
                    dpi=dpi,
                )


@click.command("init-graphics")
@with_appcontext
def init_graphics_command():
    """Clear the existing data and create new tables."""
    input_graphics_dir = "graphics"
    mk_graphics(input_graphics_dir, os.path.join(input_graphics_dir, "generated"), 300)
    click.echo("Initialized the graphics.")


def init_app(app):
    app.cli.add_command(init_graphics_command)
