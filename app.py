from aiohttp import web
from pastabin import pastabin

app = web.Application()

app.add_subapp('/pastabin/', pastabin.PastabinApp().get_app())


web.run_app(app, port=8080)
