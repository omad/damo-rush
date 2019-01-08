# Dino-Rush
Dino-Rush allow to create custom problems deck of any size and any difficulty for the game rush-hour.

The dinosaur theme, used as a mean to differentiate multiple deck, has been chosen quite arbitrary because dinosaur are cool!

# Limitation known
The size of the input svg in the repo and some constant in the code are specificaly chosen and hardcoded, as the generated image will be printed on a specific sized card.

I aim to use [printerstudio](www.printerstudio.com) for this, with the 'bridge' size card.

I didn't reuse/code a solver as I feel that having the solution printed on the back of the card is pretty useless. This also free the place and allow me to print twice more problems per deck !

# Usage
## Dependancy installation
```sh
pip3 install --upgrade --user cairosvg pillow
```

## Graphics generation
This needs to be done once initialy and everytime you change the svg graphics or add one:
```sh
./generate_graphics.py
```

## Standalon card
Makes a random card show up:
```sh
./mkcard.py
```

Same but chose number of move required (must be <= 60):
```sh
./mkcard.py --level 42
```
## Deck generation
TODO

# Credits
See dedicated file [here](credits.md).

The credits are separated to allow the automatic rendering of a specific card with credits on the deck.
