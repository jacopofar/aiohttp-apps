from aiohttp import web
from pastabin import pastabin
from metrics import metrics
import aiohttp

import config
app = web.Application()
app['config'] = config
# load global configuration
# nested applications are in their respective folder, to make easier to split them
app.add_subapp('/pastabin/', pastabin.PastabinApp().get_app(app))
app.add_subapp('/metrics/', metrics.MetricsApp().get_app(app))


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            print(f'there was an exception processing {request.rel_url}!')
            print(ex)
            return aiohttp.web.Response(status=500, text='This is a middleware and I saw an exception!')

    return middleware_handler

app.middlewares.append(error_middleware)
web.run_app(app, port=config.web_port)
