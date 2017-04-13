from aiohttp import web
import aiohttp
from os import path
from sqlalchemy import create_engine, select
from sqlalchemy import Table, Column, String, MetaData, ForeignKey, Boolean
import datetime
from json import decoder
from base64 import b64decode
engine = create_engine('sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'metrics.db'), echo=True)
conn = engine.connect()

metadata = MetaData()

trackpoints = Table('track_codes', metadata,
                    Column('code', String, primary_key=True),
                    Column('content', String),
                    Column('redirect', String),
                    Column('is_image', Boolean)
                    )

visits = Table('visits', metadata,
               Column('track_id', None, ForeignKey('track_codes.code')),
               Column('timestamp', String),
               Column('user_agent', String),
               Column('IP', String),
               Column('metadata', String),
               )
metadata.create_all(engine)


def after_authentication(mode='JUST_USERNAME'):
    def decorator(original_handler):
        async def new_fun(request):
            payload = request.get('signed_payload')
            if payload is None:
                return aiohttp.web.Response(status=403,
                                            text='Sorry, you are not authenticated')
            if mode == 'JUST_USERNAME':
                if 'u' not in payload:
                    return aiohttp.web.Response(status=403,
                                                text='Sorry, invalid authentication, no username')
                return await original_handler(request)
            print(f'UNKNOWN AUTHENTICATION MODE {mode}')
            return aiohttp.web.Response(status=500,
                                        text=f'Sorry, authentication mode {mode} in unknown')

        return new_fun

    return decorator

class MetricsApp():
    def get_app(self, parent_app):

        metrics = web.Application()
        metrics['aiohttp_jinja2_environment'] = parent_app['aiohttp_jinja2_environment']

        async def get_tracker(request):
            track_id = request.match_info['tracker']
            trackpoint = conn.execute(select([trackpoints]).where(trackpoints.c.code == track_id)).fetchone()
            if trackpoint is None:
                print(f'no trackpoint found for {track_id}')
                return aiohttp.web.Response(status=404, text="unknown URL")
            # try to get the IP directly
            IP = None
            peername = request.transport.get_extra_info('peername')
            if peername is not None:
                IP, _ = peername
            if 'X-Forwarded-For' in request.headers:
                IP = request.headers['X-Forwarded-For']
            if 'Forwarded' in request.headers:
                IP = request.headers['Forwarded']
            UA = request.headers.get('User-Agent', None)

            print(f'GET for trackpoint {track_id} from {IP} and user agent {UA}')

            conn.execute(visits.insert().values(track_id=track_id,
                                                timestamp=datetime.datetime.now().isoformat(),
                                                user_agent=UA,
                                                IP=IP,
                                                metadata=trackpoint.content))
            if trackpoint.redirect is None:
                if trackpoint.is_image:
                    # 1x1 red GIF
                    return aiohttp.web.Response(
                        headers={'Content-Type': 'image/gif'},
                        body=b64decode('R0lGODlhAQABAIABAP8AAP///yH5BAEAAAEALAAAAAABAAEAAAICRAEAOw=='),
                    )
                return aiohttp.web.Response(text='Is anyone there?')
            else:
                print(f'redirecting the user to {trackpoint.redirect}')
                return aiohttp.web.HTTPFound(trackpoint.redirect)

        metrics.router.add_get('/{tracker}', get_tracker, name='get_tracker')


        @after_authentication()
        async def add_tracker(request):
            result = None
            try:
                result = await request.json()
            except decoder.JSONDecodeError as je:
                return aiohttp.web.Response(text=f'error decoding JSON: {je}', status=400)
            if 'code' not in result:
                return aiohttp.web.Response(text=f'no "code" field in JSON request!', status=400)
            if conn.execute(select([trackpoints]).where(trackpoints.c.code == result['code'])).fetchone() is None:
                            conn.execute(trackpoints.insert().values(
                                code=result['code'],
                                redirect=result.get('redirect', None),
                                content=result.get('content', None),
                                is_image=result.get('is_image', None),
                                ))
                            return aiohttp.web.Response(text='Endpoint added: ' + str(
                                metrics.router['get_tracker'].url_for(tracker=result['code'])))

            else:
                conn.execute(trackpoints.update().where(trackpoints.c.code == result['code'])
                             .values(redirect=result.get('redirect', None),
                                     content=result.get('content', None),
                                     is_image=result.get('is_image', None),
                                    ))
                return aiohttp.web.Response(
                    text='Endpoint updated: ' + str(metrics.router['get_tracker'].url_for(tracker=result['code'])))

        metrics.router.add_post('/', add_tracker)

        return metrics
