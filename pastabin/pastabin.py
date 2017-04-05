from aiohttp import web
import aiohttp
import hashlib
import os.path as path
from string import hexdigits
class PastabinApp():
    def get_app(self):
        pastabin = web.Application()
        pastabin.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'))

        async def see_paste(request):
            id = request.match_info['file_identifier']
            if not all(c in hexdigits for c in id):
                return aiohttp.web.Response(text=f'Error, paste {id} is unknown', status=404)
            data_dir = path.join(path.dirname(path.realpath(__file__)), 'data')
            file_path = path.join(data_dir, id)
            if not path.isfile(file_path):
                return aiohttp.web.Response(text=f'Error, paste {id} is unknown', status=404)

            with open(file_path, 'r') as fp:
                return aiohttp.web.Response(text=fp.read())


        pastabin.router.add_get('/pasta/{file_identifier}', see_paste, name='see_paste')


        async def send_paste(request):
            form_data = await request.post()
            text = form_data['pasted_text']
            m = hashlib.sha256()
            m.update(text.encode('utf8'))
            file_name = m.hexdigest()

            data_dir = path.join(path.dirname(path.realpath(__file__)), 'data')
            file_path = path.join(data_dir, file_name)
            if not path.isfile(file_path):
                with open(file_path, 'w') as fp:
                    fp.write(text)
            return aiohttp.web.HTTPFound(pastabin.router['see_paste'].url_for(file_identifier=file_name))

        pastabin.router.add_post('/send_paste', send_paste)




        pastabin.router.add_static('/', 'pastabin/static')

        return pastabin