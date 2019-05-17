# User welcome

An online instance of the web deck generator is currently available [here](http://www.dino.lagalenebleue.fr). This is probably where you want to go :)

# Note to developers

## Install
```sh
git clone clone export https://gitlab.com/crazyiop/dino-rush
cd dino-rush
pip3 install --user -r requirements.txt
```

## Running a local instance (development mode)
Some one-time configuration are needed before your first run of the web server:
```sh
export FLASK_APP=dino
flask init-db # will take a few minutes
flask init-graphics
```

Afterwards run the server with:
```sh
export FLASK_APP=dino
flask run
```

## Running a web instance
My choice is to use nginx/uwsgi.

todo...
