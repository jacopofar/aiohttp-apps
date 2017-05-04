from aiohttp import web
import aiohttp
from os import path, makedirs
from grammo.sample_generator import sample_generator
import re
digits_pattern = re.compile("^[0-9]+$")

# helper to retrieve clean text from a grammar

def to_clean_text(tokens):
    clean_tokens = []
    for i, t in enumerate(tokens):
        if i > 0:
            if digits_pattern.match(t) and digits_pattern.match(tokens[i - 1]):
                clean_tokens.extend(t)
                continue
            if t[0] == ',':
                clean_tokens.extend(t)
                continue
            # do not use spaces when the previous token ends with -+-
            if tokens[i - 1][-3:] == '-+-':
                # remove trailing -+-
                if t[-3:] == '-+-':
                    clean_tokens.extend(t[:-3])
                else:
                    clean_tokens.extend(t)
                continue
        # remove trailing -+-
        if t[-3:] == '-+-':
            clean_tokens.extend(' ' + t[:-3])
        else:
            clean_tokens.extend(' ' + t)
    return ''.join(clean_tokens)


class GrammoApp():

    def __init__(self):
        # the grammar object, each one si a file in grammars folder
        self.gens = {}

    def get_app(self, parent_app):
        grammo = web.Application()
        grammar_dir = path.join(path.abspath(path.dirname(__file__)), 'grammars')
        snippets_dir = path.join(path.abspath(path.dirname(__file__)), 'snippets')

        grammo['use_main_app_error_pages'] = False

        def get_grammar(name):
            with open(path.join(grammar_dir, name + '.fcfg'), 'r', encoding='utf8') as grammar_file:
                return grammar_file.read()

        def get_snippet(name):
            with open(path.join(snippets_dir, name), 'r', encoding='utf8') as this_snippet:
                return this_snippet.read()

        def generate_production(grammar, seed):
            if grammar not in self.gens:
                self.gens[grammar] = sample_generator.SampleGenerator(get_grammar(grammar))

            tokens = self.gens[grammar].generate(seed)[1]
            result = []
            for i, t in enumerate(tokens):
                if str.startswith(t, '{{snippet:') and str.endswith(t, '}}'):
                    result.append(get_snippet(t[len('{{snippet:'): -len('}}')]))
                    continue
                if str.startswith(t, '{{grammar:') and str.endswith(t, '}}'):
                    result.extend(generate_production(t[len('{{grammar:'): -len('}}')], seed + '_' + str(i)))
                    continue
                result.append(t)
            print(result)
            return result

        async def get_production(request):
            seed = request.match_info['seed']
            tokens = generate_production('base', seed)
            html = to_clean_text(tokens)
            return aiohttp.web.Response(body=html, status=200, headers={
                    'Content-Type': 'text/html; charset=utf-8'
                })

        grammo.router.add_get('/{seed}', get_production, name='get_production')
        return grammo
