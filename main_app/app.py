from aiohttp import web
import asyncio

from pastabin import pastabin
from metrics import metrics
from shinymd import shinymd
from rawchat import rawchat
from grammo import grammo

from time import gmtime
import aiohttp
import jwt
import jinja2
import aiohttp_jinja2
import os.path as path
import config
import logging

from pathlib import Path

app = web.Application()
app['config'] = config


template_folder = str(Path(__file__).parent / 'assets' / 'jinja_templates')
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_folder), app_key='root_app_jinja2_environment')

# load global configuration
# nested applications are in their respective folders, to make easier to split them
app.add_subapp('/pastabin', pastabin.PastabinApp().get_app(app))
app.add_subapp('/metrics', metrics.MetricsApp().get_app(app))
app.add_subapp('/shinymd', shinymd.ShinymdApp().get_app(app))
app.add_subapp('/rawchat', rawchat.RawchatApp().get_app(app))
app.add_subapp('/grammo', grammo.GrammoApp().get_app(app))


async def error_middleware(this_app, handler):
    async def middleware_handler(request):
        # the error pages are used only when the nested app explicitly delegates to use them
        # or there's just no nested app to call (unknown URL)
        if request.app is app or request.app['use_main_app_error_pages']:
            try:
                    return await handler(request)

            except aiohttp.web_exceptions.HTTPNotFound as ex:
                request.app['root_app_jinja2_environment'] = app['root_app_jinja2_environment']
                response = aiohttp_jinja2.render_template('404.jinja2',
                                                          request,
                                                          {'a': 'b'},
                                                          app_key='root_app_jinja2_environment',)
                response.set_status(404)
                return response
            except aiohttp.web_exceptions.HTTPForbidden as ex:
                request.app['root_app_jinja2_environment'] = app['root_app_jinja2_environment']
                logging.warning(f'there was an HTTP exception processing {request.rel_url}!')
                logging.warning(ex)
                response = aiohttp_jinja2.render_template('403.jinja2',
                                                          request,
                                                          {'a': 'b'},
                                                          app_key='root_app_jinja2_environment',)
                response.set_status(403)
                return response

            except aiohttp.web_exceptions.HTTPForbidden as ex:
                request.app['root_app_jinja2_environment'] = app['root_app_jinja2_environment']
                print(f'there was an HTTP exception processing {request.rel_url}!')
                print(ex)
                print(type(ex))
                response = aiohttp_jinja2.render_template('500.jinja2',
                                                          request,
                                                          {'a': 'b'},
                                                          app_key='root_app_jinja2_environment',)
                response.set_status(500)
                return response
        else:
            # no error page delegation, the middleware does not intervene
            return await handler(request)

    return middleware_handler


app.middlewares.append(error_middleware)


async def jwt_middleware(this_app, handler):
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

app.router.add_static('/static', str(Path(__file__).parent / 'assets' / 'static'))

# set logging time to UTC
logging.Formatter.converter = gmtime
# see https://stackoverflow.com/questions/43500983/specify-log-request-format-in-aiohttp-2
app_logger = logging.getLogger('aiohttp.access')
app_logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
app_logger.addHandler(ch)


app.router.add_get('/', lambda r: aiohttp.web.HTTPFound('/static/index.html'))
app.router.add_get('/robots.txt', lambda r: aiohttp.web.HTTPFound('/static/robots.txt'))

# explicitly retrieve and use the loop instead of just using web.run_app, to apply a custom logger
loop = asyncio.get_event_loop()

loop.run_until_complete(
    loop.create_server(
        app.make_handler(access_log=app_logger,
                         access_log_format='%t %s %r %b'), '0.0.0.0', config.web_port))
loop.run_forever()
loop.close()
