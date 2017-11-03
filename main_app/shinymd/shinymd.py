from aiohttp import web
import aiohttp
import json
from os import path, makedirs
from markdown2 import Markdown
from pathlib import Path

class ShinymdApp():
    def get_app(self, parent_app):
        shinymd = web.Application()
        data_dir = path.join(parent_app['config'].data_folder, 'shinymd_data')
        makedirs(data_dir, exist_ok=True)
        shinymd['use_main_app_error_pages'] = False
        shinymd.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'), name='index')
        # this is to manage an URL without the trailing /
        shinymd.router.add_get('', lambda r: aiohttp.web.HTTPFound(str(shinymd.router['index'].url_for()) + 'index.html'))

        async def see_article(request):
            page_id = request.match_info['file_identifier']
            file_path = path.realpath(path.join(data_dir, page_id))
            if path.commonpath([data_dir, file_path]) != data_dir:
                print(f'unacceptable path: {page_id}')
                return aiohttp.web.Response(text=f'Error, page {page_id} is unknown', status=404)

            if not path.isfile(file_path):
                return aiohttp.web.Response(text=f'Error, page {page_id} is unknown', status=404)

            with open(file_path, 'r') as fp:
                page_structure = json.loads(fp.read())
                return aiohttp.web.Response(body=page_structure['html_content'], headers={
                    'Content-Type': 'text/html; charset=utf-8'
                })

        shinymd.router.add_get('/page/{file_identifier}', see_article, name='see_page')

        async def publish_page(request):
            form_data = await request.post()
            text = form_data['page_md']
            page_id = form_data['page_id']

            file_path = path.realpath(path.join(data_dir, page_id))
            if path.commonpath([data_dir, file_path]) != data_dir:
                print(f'proposed an unacceptable path: {page_id}')
                return aiohttp.web.Response(text=f'Error, {page_id} is not a valid name', status=404)

            if not path.isfile(file_path):
                with open(file_path, 'w') as fp:
                    obj = {}
                    markdowner = Markdown()
                    obj['html_content'] = markdowner.convert(text)
                    fp.write(json.dumps(obj))
            return aiohttp.web.HTTPFound(shinymd.router['see_page'].url_for(file_identifier=page_id))

        shinymd.router.add_post('/publish_page', publish_page)

        shinymd.router.add_static('/', str(Path(__file__).parent / 'static'))

        return shinymd
