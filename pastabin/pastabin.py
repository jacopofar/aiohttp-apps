from aiohttp import web
import aiohttp
import hashlib
from os import path, makedirs
from string import hexdigits


class PastabinApp():
    def get_app(self, parent_app):
        pastabin = web.Application()
        data_dir = path.join(parent_app['config'].data_folder, 'pastabin_data')
        makedirs(data_dir, exist_ok=True)
        pastabin['use_main_app_error_pages'] = True
        pastabin.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'), name='index')
        # this is to manage an URL without the trailing /
        pastabin.router.add_get('', lambda r: aiohttp.web.HTTPFound(str(pastabin.router['index'].url_for()) + 'index.html'))
        async def see_paste(request):
            paste_id = request.match_info['file_identifier']
            if not all(c in hexdigits for c in paste_id):
                return aiohttp.web.Response(text=f'Error, paste {paste_id} is unknown', status=404)

            file_path = path.join(data_dir, paste_id)
            if not path.isfile(file_path):
                return aiohttp.web.Response(text=f'Error, paste {paste_id} is unknown', status=404)

            with open(file_path, 'r') as fp:
                return aiohttp.web.Response(text=fp.read())


        pastabin.router.add_get('/pasta/{file_identifier}', see_paste, name='see_paste')


        async def send_paste(request):
            form_data = await request.post()
            text = form_data['pasted_text']
            m = hashlib.sha256()
            m.update(text.encode('utf8'))
            file_name = m.hexdigest()
            file_path = path.join(data_dir, file_name)
            if not path.isfile(file_path):
                with open(file_path, 'w') as fp:
                    fp.write(text)
            return aiohttp.web.HTTPFound(pastabin.router['see_paste'].url_for(file_identifier=file_name))

        pastabin.router.add_post('/send_paste', send_paste)


        pastabin.router.add_static('/', 'pastabin/static')

        return pastabin