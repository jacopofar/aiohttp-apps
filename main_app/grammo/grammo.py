from aiohttp import web
import aiohttp
from os import path, makedirs
from grammo.sample_generator.generator import Generator
from pathlib import Path

class GrammoApp:

    def __init__(self):
        # the grammar object, each one si a file in grammars folder
        self.gens = {}

    @staticmethod
    def get_app(parent_app):
        grammo = web.Application()
        grammar_dir = path.join(path.abspath(path.dirname(__file__)), 'grammars')
        snippets_dir = path.join(path.abspath(path.dirname(__file__)), 'snippets')
        templates_dir = path.join(path.abspath(path.dirname(__file__)), 'templates')

        generator = Generator(grammar_dir, snippets_dir, templates_dir)
        grammo['use_main_app_error_pages'] = False

        async def get_production(request):
            seed = request.match_info['seed']
            html = generator.generate(seed)
            return aiohttp.web.Response(body=html, status=200, headers={
                    'Content-Type': 'text/html; charset=utf-8'
                })

        grammo.router.add_get('/{seed}', get_production, name='get_production')
        grammo.router.add_static('/static', str(Path(__file__).parent / 'static'))

        return grammo
