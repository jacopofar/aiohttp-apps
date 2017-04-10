from aiohttp import web
import aiohttp
from os import path
from sqlalchemy import create_engine, select
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime
import datetime

engine = create_engine('sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'metrics.db'), echo=True)
conn = engine.connect()

metadata = MetaData()

trackpoints = Table('track_codes', metadata,
                    Column('code', String, primary_key=True),
                    Column('content', String),
                    Column('redirect', String)
                    )

visits = Table('visits', metadata,
               Column('track_id', None, ForeignKey('track_codes.code')),
               Column('timestamp', String),
               Column('user_agent', String),
               Column('IP', String),
               Column('metadata', String),
               )
metadata.create_all(engine)


class MetricsApp():
    def get_app(self, parent_app):

        def after_authentication(auth_params=None):
            def decorator(original_handler):
                async def new_fun(request):
                    candidate_token = request.headers.get('X-TOKEN', request.query.get('token', None))
                    print(f'candidate token for {request.rel_url} is {candidate_token}')
                    parent_app['config'].secret_token
                    if candidate_token != parent_app['config'].secret_token:
                        return aiohttp.web.Response(status=404,
                                                    text='Hello, this is a decorator and I refused the unauthenticated request ')
                    return await original_handler(request)

                return new_fun

            return decorator

        metrics = web.Application()

        @after_authentication()
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
                return aiohttp.web.Response(text='nisba')
            else:
                print(f'redirecting the user to {trackpoint.redirect}')
                return aiohttp.web.HTTPFound(trackpoint.redirect)

        metrics.router.add_get('/{tracker}', get_tracker)
        return metrics
