from aiohttp import web
import aiohttp
from os import path, makedirs
import socketio
from html import escape
import re
from pathlib import Path

sio = socketio.AsyncServer(async_mode='aiohttp')


class RawchatApp():
    def get_app(self, parent_app):
        rooms = {}
        rawchat = web.Application()
        sio.attach(parent_app)
        data_dir = path.join(parent_app['config'].data_folder, 'rawchat_data')
        makedirs(data_dir, exist_ok=True)
        rawchat['use_main_app_error_pages'] = True
        rawchat.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'), name='index')
        # this is to manage an URL without the trailing /
        rawchat.router.add_get('', lambda r: aiohttp.web.HTTPFound(str(rawchat.router['index'].url_for()) + 'index.html'))

        def render_message(raw_input):
            safe_text = escape(raw_input)
            enriched_html = re.sub(r"((http://|https://)[^ ]+)", r'<a href="\1">\1</a>', safe_text)
            return enriched_html


        @sio.on('join', namespace='/rawchat')
        async def join(sid, message):
            if len(message['nick']) > 30:
                await sio.emit('alert',
                         {'message': 'nickname too long, use less than 30 characters'},
                         room=sid,
                         namespace='/rawchat')
                return
            print('join by ' + str(sid) + ' to room ' + message['room'])

            if message['room'] not in rooms:
                rooms[message['room']] = {'users': [message['nick']]}
            else:
                for u in rooms[message['room']]['users']:
                    await sio.emit('join',
                                   {'nick': u},
                                   room=sid,
                                   namespace='/rawchat')
                rooms[message['room']]['users'].append(message['nick'])

            sio.enter_room(sid, message['room'], namespace='/rawchat')
            await sio.emit('join',
                           {'nick':  message['nick']},
                           room=message['room'],
                           namespace='/rawchat')

        @sio.on('message', namespace='/rawchat')
        async def message(sid, message):
            if len(message['nick']) > 30:
                await sio.emit('alert',
                         {'message': 'please do not tamper with the chat :('},
                         room=sid,
                         namespace='/rawchat')
                return
            message['message'] = render_message(message['message'])
            if len(message['message']) > 400:
                message['message'] = message['message'][:400] + '...'
            print('message by ' + str(sid) + ':' + str(message))
            await sio.emit('message',
                           {'message': message['message'],
                                       'nick': message['nick']},
                           room=message['room'],
                           namespace='/rawchat')


        rawchat.router.add_static('/', str(Path(__file__).parent / 'static'))

        return rawchat
