from aiohttp import web
import aiohttp
import json
import os.path as path
from markdown2 import Markdown

class ShinymdApp():
    def get_app(self, parent_app):
        shinymd = web.Application()
        shinymd.router.add_get('/', lambda r: aiohttp.web.HTTPFound('index.html'))

        async def see_article(request):
            id = request.match_info['file_identifier']
            data_dir = path.join(path.dirname(path.realpath(__file__)), 'data')
            file_path = path.realpath(path.join(data_dir, id))
            if path.commonpath([data_dir, file_path]) != data_dir:
                print(f'unacceptable path: {id}')
                return aiohttp.web.Response(text=f'Error, page {id} is unknown', status=404)

            if not path.isfile(file_path):
                return aiohttp.web.Response(text=f'Error, page {id} is unknown', status=404)

            with open(file_path, 'r') as fp:
                page_structure = json.loads(fp.read())
                return aiohttp.web.Response(body=page_structure['html_content'], headers={'Content-Type': 'text/html; charset=utf-8'})

        shinymd.router.add_get('/page/{file_identifier}', see_article, name='see_page')


        async def publish_page(request):
            form_data = await request.post()
            text = form_data['page_md']
            id = form_data['page_id']

            data_dir = path.join(path.dirname(path.realpath(__file__)), 'data')
            file_path = path.realpath(path.join(data_dir, id))
            if path.commonpath([data_dir, file_path]) != data_dir:
                print(f'proposed an unacceptable path: {id}')
                return aiohttp.web.Response(text=f'Error, {id} is not a valid name', status=404)

            if not path.isfile(file_path):
                with open(file_path, 'w') as fp:
                    obj = {}
                    markdowner = Markdown()
                    obj['html_content'] = markdowner.convert(text)
                    fp.write(json.dumps(obj))
            return aiohttp.web.HTTPFound(shinymd.router['see_page'].url_for(file_identifier=id))

        shinymd.router.add_post('/publish_page', publish_page)

        shinymd.router.add_static('/', 'shinymd/static')

        return shinymd