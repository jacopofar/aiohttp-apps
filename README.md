# aiohttp 2 demo applications
[Aiohttp](https://github.com/aio-libs/aiohttp) is a very interesting tool and with version 2 with libuv is considerably faster.
This repository shows a few example applications implemented (or to be implemented) with it.

Those are:

* pastabin, a paste service (✔✔✔︎ done)
* a chat system with websockets (✔✔✔︎ done)
* micro publish system (✔✔✔︎ done)
* mastodon OAuth2 checker 
* metric collector (to collect metrics about page visits or QR codes usage) (✔✔✔ done)
* a tool to track the content at a given URL at the current time (screenshot or page HTML)
* generate pages based on the [NLTK-grammar sampler](https://github.com/jacopofar/django-nltk-generator) (✔✔✔︎ done)
* an application to build an image ranking by extracting random pairs and letting users vote between them
* an application to allow users to tag images and add description

## Install and run
The repository is published as a Docker image ready to use: `docker run -p 8080:8080 jacopofar/aiohttp-apps`

Otherwise:
* Python 3.6 or above is required, you also need `pip3`.
* Create a virtualenv with `python3 -m venv .venv`
* Activate it with `source .venv/bin/activate`
* Install with `pip3 install -r requirements.txt`
* Run with `DYNACONF_PORT=8090 python3 app.py` (omitting the port it uses 8080)

Tested on MacOS and a few Linux distros, if you have a Windows machine and are interested I'd like to have it work there as well 
