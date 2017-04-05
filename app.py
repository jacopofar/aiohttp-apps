from aiohttp import web
from pastabin import pastabin
from metrics import metrics
import config
app = web.Application()
app['config'] = config
# load global configuration
# nested applications are in their respective folder, to make easier to split them
app.add_subapp('/pastabin/', pastabin.PastabinApp().get_app())
app.add_subapp('/metrics/', metrics.MetricsApp().get_app())

web.run_app(app, port=config.web_port)