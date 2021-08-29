import os
import shutil
import threading
from io import BytesIO
from zipfile import ZipFile

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_from_directory,
    redirect,
    abort,
    send_file,
)
from flask_wtf import FlaskForm
from wtforms import RadioField, DecimalField
from wtforms.validators import DataRequired, NumberRange

from dino.db import get_db
from dino.generator import cards

generator = Blueprint("generator", __name__)
running_processes = {}


def _deck_id_from_args(args):
    limits = ""
    for el, (low, high) in args["limits"].items():
        limits += f"-{low},{high}"

    return (
        f"{args['icon']}-{args['nb_move']}-{args['index_move']}-"
        f"{args['n']}-{args['step']}{limits}"
    )


def _get_list_info(deck_id):
    icon, nb_move, index_move, n, step, *limits = deck_id.split("-")
    res = {
        "icon": icon,
        "nb_move": int(nb_move),
        "index_move": int(index_move),
        "n": int(n),
        "step": 1,
        "url": deck_id + ".zip",
        "deck_id": deck_id,
    }

    for el, limit in zip(["cars", "trucks", "walls"], limits):
        low, high = limit.split(",")
        res[el] = (int(low), int(high))

    return res


class ExportingThread(threading.Thread):
    def __init__(self, rows, args):
        super().__init__()
        self.rows = rows
        self.args = args

    def run(self):
        if not os.path.exists("deck_output"):
            os.makedirs("deck_output")

        deck_file = os.path.join("deck_output", f"{self.args['deck_id']}.zip")
        if os.path.exists(deck_file):
            print("exit cards generation thread: deck.zip exist")
            return

        # TODO delete oldest zip if total space taken too high

        cards_dir = os.path.join("deck_output", str(self.args["deck_id"]))

        if os.path.exists(cards_dir):
            print("cards generation thread: card folder exist, removing it")
            shutil.rmtree(cards_dir)

        os.makedirs(cards_dir)

        with ZipFile(deck_file + ".tmp", "w") as myzip:
            # front title card
            card = cards.generate_front_title_card(self.args["icon"])
            card_filename = "front.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card_arcname = os.path.join(
                "recto", f"{0:0{len(str(1 + self.args['n'] // 2))}d}.png"
            )
            card.save(card_filepath, "PNG")
            myzip.write(card_filepath, arcname=card_arcname)

            # back title card
            card = cards.generate_back_title_card()
            card_filename = "back.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card_arcname = os.path.join(
                "verso", f"{0:0{len(str(1 + self.args['n'] // 2))}d}.png"
            )
            card.save(card_filepath, "PNG")
            myzip.write(card_filepath, arcname=card_arcname)

            for i, row in enumerate(self.rows):
                side = "verso" if i % 2 else "recto"
                card_filename = f"{i + 1}.png"
                print(f"[gen] {card_filename}")
                card_arcname = os.path.join(
                    side, f"{1 + i // 2:0{len(str(1 + self.args['n'] // 2))}d}.png"
                )

                card_filepath = os.path.join(cards_dir, card_filename)
                deck_info = {
                    "icon": self.args["icon"],
                    "text": f"{i + 1:0{len(str(self.args['n']))}d}",
                }

                card = cards.generate_puzzle_card(row, deck_info)
                card.save(card_filepath, "PNG")
                myzip.write(card_filepath, arcname=card_arcname)

                print(
                    f"[Card] {self.args['icon']} {i + 1} generated "
                    f"({row['nb_move']}, {row['index_']}/{row['index_max']})"
                )

            card, n_next = cards.generate_front_score_card(
                self.args["icon"], 1, self.args["n"]
            )
            card_filename = "score_front.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card.save(card_filepath, "PNG")
            card_arcname = os.path.join("recto", f"99.png")
            myzip.write(card_filepath, arcname=card_arcname)

            if n_next != self.args["n"]:
                card = cards.generate_back_score_card(
                    self.args["icon"], n_next, self.args["n"]
                )
            else:
                card = cards.generate_front_title_card(self.args["icon"])
            card_filename = "score_back.png"
            card_filepath = os.path.join(cards_dir, card_filename)
            card.save(card_filepath, "PNG")
            card_arcname = os.path.join("verso", f"99.png")
            myzip.write(card_filepath, arcname=card_arcname)

        shutil.rmtree(cards_dir)
        os.rename(deck_file + ".tmp", deck_file)
        self.step = "done"


@generator.route("/list")
def list_deck():
    if not os.path.exists("deck_output"):
        os.makedirs("deck_output")

    files = [f for f in os.listdir("deck_output") if f.endswith(".zip")]
    return render_template("list.html", files=files)


@generator.route("/api/list")
def api_list_deck():
    files = [
        _get_list_info(os.path.splitext(f)[0])
        for f in os.listdir("deck_output")
        if f.endswith(".zip")
    ]
    return jsonify(files)


@generator.route("/dl/<path:path>")
def dl_deck(path):
    if os.path.isfile(os.path.join("deck_output", path)):
        con = get_db()
        c = con.cursor()
        c.execute("select * from dl_count where id = ?", (path,))
        res = c.fetchone()
        if res is None:
            c.execute("insert into dl_count (id, nb) values (?, ?)", (path, 1))
        else:
            c.execute("update dl_count set nb = ? where id = ?", (res["nb"] + 1, path))
        con.commit()
        return send_from_directory(directory="../deck_output", filename=path)

    if os.path.isfile(os.path.join("graphics", "static", "dino", path)):
        return send_from_directory(directory="../graphics/static/dino", filename=path)

    abort(404)


class DeckForm(FlaskForm):
    icon = RadioField(
        "icon",
        choices=[
            ("stegosaurus", "stegosaurus"),
            ("brontosaurus", "brontosaurus"),
            ("elasmosaurus", "elasmosaurus"),
            ("ichthyosaurus", "ichthyosaurus"),
            ("parasaurolophus", "parasaurolophus"),
        ],
        default="stegosaurus",
        validators=[DataRequired()],
    )
    nb_move = DecimalField(
        "nb_move", validators=[NumberRange(2, 60)], render_kw={"value": 60}
    )
    index_move = DecimalField("index_move", validators=[], render_kw={"value": 1})
    n = DecimalField("n", validators=[NumberRange(1, 84)], render_kw={"value": 84})
    step = DecimalField("step", validators=[], render_kw={"value": 1, "disabled": ""})
    car_min = DecimalField(
        "car_min", validators=[NumberRange(2, 17)], render_kw={"value": 2}
    )
    car_max = DecimalField(
        "car_max", validators=[NumberRange(2, 17)], render_kw={"value": 17}
    )
    truck_min = DecimalField(
        "truck_min", validators=[NumberRange(0, 10)], render_kw={"value": 0}
    )
    truck_max = DecimalField(
        "truck_max", validators=[NumberRange(0, 10)], render_kw={"value": 4}
    )
    wall_min = DecimalField(
        "wall_min", validators=[NumberRange(0, 2)], render_kw={"value": 0}
    )
    wall_max = DecimalField(
        "wall_max", validators=[NumberRange(0, 2)], render_kw={"value": 0}
    )


@generator.route("/gen/")
@generator.route("/gen")
@generator.route("/gen/submit_deck", methods=("GET", "POST"))
def submit():
    form = DeckForm(request.form)
    if form.validate_on_submit():
        args = {
            "nb_move": form.nb_move.data,
            "index_move": form.index_move.data,
            "icon": form.icon.data,
            "n": form.n.data,
            "step": form.step.data,
            "limits": {
                "cars": (form.car_min.data, form.car_max.data),
                "trucks": (form.truck_min.data, form.truck_max.data),
                "wall": (form.wall_min.data, form.wall_max.data),
            },
        }
        deck_id = _deck_id_from_args(args)
        return redirect("/gen/build/" + deck_id)
    return render_template("deck_form.html", form=form)


@generator.route("/gen/build/<string:deck_id>")
def build(deck_id):
    return render_template("build.html", deck_id=deck_id)


@generator.route("/api/new_deck/<string:deck_id>")
def build_deck(deck_id):
    args = _get_list_info(deck_id)
    print(args)
    cars = sorted(list(args["cars"]))
    trucks = sorted(list(args["trucks"]))
    walls = sorted(list(args["walls"]))

    c = get_db().cursor()

    c.execute(
        "select * from games where nb_move = ? and index_ = ?",
        (args["nb_move"], args["index_move"]),
    )

    # Test if asked starting pos exist
    row = c.fetchone()
    if row is None:
        args["nb_move"] -= 1
        args["index_move"] = 1

    print(row)
    c.execute(
        """
        select * from games
        where nb_wall between ? and ?
        and nb_car between ? and ?
        and nb_truck between ? and ?
         limit ?
        """,
        (*walls, *cars, *trucks, args["n"] + 1),
    )

    *rows, next_row = c.fetchall()
    args["n"] = len(rows)
    args["next"] = (next_row["nb_move"], next_row["index_"])

    global running_processes
    running_processes[deck_id] = ExportingThread(rows, args)
    running_processes[deck_id].start()
    return jsonify({"id": deck_id, "step": "starting_generation", "percent": 0})


@generator.route("/api/status/<string:deck_id>")
def status(deck_id):
    tmp_path = os.path.join("deck_output", f"{deck_id}")
    if os.path.exists(tmp_path):
        files = os.listdir(tmp_path)
        percent = int(100 * len(files) / _get_list_info(deck_id)["n"])
        return jsonify({"id": deck_id, "step": "in_preparation", "percent": percent})

    return jsonify({"id": deck_id, "step": "done", "percent": 100})


@generator.route("/random")
def random():
    min_moves = request.args.get('min', 6)
    max_moves = request.args.get('max', 24)
    card = random_card_image(min_moves, max_moves)

    return send_file(card, mimetype='image/png', as_attachment=False)


def random_card_image(min_moves, max_moves):
    c = get_db().cursor()
    c.execute("""
    with LIMITS as (
        -- Rows are ordered id min id = hardest
        select min(id) as hardest, max(id) as easiest
        from games
        where nb_move <= ? and nb_move >= ?
    )
    select *
    from games
    where id > (
        select abs(random()) % ((select easiest from LIMITS) - (select hardest from LIMITS)) + (select hardest from LIMITS)
    ) and nb_wall = 0
    and nb_truck <= 4
    and nb_car <= 7
    limit 1;
   """, (max_moves, min_moves))
    # Test if asked starting pos exist
    row = c.fetchone()
    card = cards.generate_puzzle_card(row)

    output = BytesIO()
    card.convert('RGBA').save(output, format='PNG')
    output.seek(0, 0)
    return output


@generator.route("/test")
def test():
    return jsonify({"args": request.args})


@generator.route("/card/<string:card_id>")
def show_card(card_id):
    c = get_db().cursor()

    c.execute(
        "select * from games where id = ?",
        (int(card_id),),
    )

    # Test if asked starting pos exist
    row = c.fetchone()

    card = cards.generate_puzzle_card(row)

    return send_file(card, mimetype='image/png', as_attachment=False)


@generator.route("/pdf")
def generate_pdf():
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import pink, black
    c = canvas.Canvas('myfile.pdf', pagesize=landscape(A4))
    width, height = landscape(A4)
    for i in range(8):
        num_moves = i + 6
        card = ImageReader(random_card_image(num_moves, num_moves))
        row = 1 if i <= 3 else 0
        col = i % 4
        c.drawImage(card,
                         x=(col * 75 * mm) - 1.5 * mm,
                         y=(100 * mm * row) + 5 * mm,
                         width=75 * mm, height=100 * mm)
    c.setStrokeColor(black)
    # draw some lines
    c.grid([(75*mm*x)-1.5*mm for x in range(6)], [0*mm, 105*mm, 210*mm])
    c.showPage()
    c.save()
    return send_file('../myfile.pdf', mimetype='application/pdf')
