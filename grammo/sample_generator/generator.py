from os import path
from functools import lru_cache
from . import grammar_generator
from jinja2 import Environment, meta

import re

digits_pattern = re.compile("^[0-9]+$")

class Generator():

    def __init__(self, grammar_dir, snippets_dir, templates_dir):
        self.grammar_dir = grammar_dir
        self.snippets_dir = snippets_dir
        self.templates_dir = templates_dir

        self.gens = {}

    def get_grammar(self, name):
        with open(path.join(self.grammar_dir, name + '.fcfg'), 'r', encoding='utf8') as grammar_file:
            return grammar_file.read()

    def get_snippet(self, name):
        with open(path.join(self.snippets_dir, name), 'r', encoding='utf8') as this_snippet:
            return this_snippet.read()

    def get_template(self, name):
        with open(path.join(self.templates_dir, name), 'r', encoding='utf8') as this_template:
            raw_template = this_template.read()
            env = Environment()
            ast = env.parse(raw_template)
            return meta.find_undeclared_variables(ast), env.from_string(raw_template)

    # helper to retrieve clean text from a grammar
    @staticmethod
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

    def fill_template(self, template, seed):
        variables, template = self.get_template(template)
        to_replace = {}
        for i, gram in enumerate(variables):
            to_replace[gram] = self.to_clean_text(self.generate_production(gram, seed + '_' + str(i) ))
        return template.render(to_replace)

    def expand_token(self, t, seed):
        if str.startswith(t, '{{snippet:') and str.endswith(t, '}}'):
            return [self.get_snippet(t[len('{{snippet:'): -len('}}')])]

        if str.startswith(t, '{{grammar:') and str.endswith(t, '}}'):
            return self.generate_production(t[len('{{grammar:'): -len('}}')], seed)

        if str.startswith(t, '{{template:') and str.endswith(t, '}}'):
            return [self.fill_template(t[len('{{template:'): -len('}}')], seed)]
        return [t]

    @lru_cache(maxsize=200)
    def generate_production(self, grammar, seed):
        if grammar not in self.gens:
            self.gens[grammar] = grammar_generator.GrammarGenerator(self.get_grammar(grammar))

        tokens = self.gens[grammar].generate(seed)[1]
        result = []
        for i, t in enumerate(tokens):
            result.extend(self.expand_token(t, seed + '_' + str(i)))

        print(result)
        return result

    def generate(self, seed):
        tokens = self.generate_production('base', seed)
        return self.to_clean_text(tokens)