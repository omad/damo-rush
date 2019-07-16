# User welcome

An online instance of the web deck generator is currently available [here](http://dino.lagalenebleue.fr). This is probably where you want to go :)

# Note to developers

## Install
```sh
git clone clone export https://gitlab.com/crazyiop/dino-rush
cd dino-rush
apt install libcairo2-dev
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
The same initial setup is needed:
```sh
export FLASK_APP=dino
flask init-db # will take a few minutes
flask init-graphics
```

To serve the website, I chose to use nginx/uwsgi.

```sh
cp dino.nginx /etc/nginx/sites-available/dino
```
create symlink to the above at /sites-enabled/dino
```sh
uwsgi --ini project.ini
```

### additional setup
dns zone -> add a cname entry, which target the main domain.
