from aiohttp import web
from pastabin import pastabin
from metrics import metrics
from shinymd import shinymd

import aiohttp
import jwt
import jinja2
import aiohttp_jinja2
import os.path as path


import config
app = web.Application()
app['config'] = config


aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(path.join(path.dirname(path.dirname(__file__)), 'assets/jinja_templates')))

# load global configuration
# nested applications are in their respective folder, to make easier to split them
app.add_subapp('/pastabin/', pastabin.PastabinApp().get_app(app))
app.add_subapp('/metrics/', metrics.MetricsApp().get_app(app))
app.add_subapp('/shinymd/', shinymd.ShinymdApp().get_app(app))



async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            return await handler(request)
        except aiohttp.web_exceptions.HTTPNotFound as ex:
            response = aiohttp_jinja2.render_template('404.jinja2',
                                                      request,
                                                      {'a': 'b'})
            response.set_status(404)
            return response
        except web.HTTPException as ex:
            print(f'there was an exception processing {request.rel_url}!')
            print(ex)
            print(type(ex))
            response = aiohttp_jinja2.render_template('500.jinja2',
                                                      request,
                                                      {'a': 'b'})
            response.set_status(500)
    return middleware_handler

app.middlewares.append(error_middleware)


async def jwt_middleware(app, handler):
    async def middleware_handler(request):
        candidate_jwt = request.cookies.get('JWT', None)
        if candidate_jwt is None:
            return await handler(request)
        try:
            # the library implicitly authenticate the JWT when decoding
            signed_payload = jwt.decode(candidate_jwt, config.jwt_secret, algorithms=config.jwt_algorithms)
            request['signed_payload'] = signed_payload
            return await handler(request)
        except jwt.exceptions.DecodeError as ex:
            print(f'there was an exception processing JWT {request.rel_url}!')
            return aiohttp.web.Response(status=500, text=f'Error decoding JWT: {ex} ')
    return middleware_handler

app.middlewares.append(jwt_middleware)

app.router.add_static('/static', 'assets/static')

web.run_app(app, port=config.web_port)
