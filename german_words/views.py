import sys
import json
from collections import defaultdict

from flask import render_template, Markup

from german_words import app


def load_words(path):
    print('Loading words...', file=sys.stderr)
    d = {}
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            word = obj[0]
            d[word] = obj
    return d


def load_frequency(path):
    print('Loading freqs...', file=sys.stderr)
    with open(path) as f:
        for line in f:
            es = line.split()
            if len(es) == 2:
                word = es[1]
                yield word


pos_to_words = defaultdict(list)


def is_new_item(d):
    for e in d[1:]:
        e = e.strip()
        if e:
            return not (e == ':' or e == '*')
    return False


def join(toks):
    s = ' '.join(toks)
    s = s.replace(' ; ', '; ')
    s = s.replace(' , ', ', ')
    s = s.replace(' ( ', '( ')
    s = s.replace(' ) ', ') ')
    return s


def link(word):
    return f'<a href="https://www.linguee.de/deutsch-englisch/search?source=auto&query={word}" target="_blank">{word}</a>'


def parse_definitions(defs):
    definitions = []
    for d in defs:
        if is_new_item(d):
            toks = []
            for tok in d[1:]:
                tok = tok.strip()
                if tok.startswith('[['):
                    tok = tok[2:-2]
                if tok.startswith('{{lb|de|'):
                    tok = f"<i>({tok[len('{{lb|de|'):-2].replace('|', ', ')})</i>"
                elif tok.startswith('{{l|en|'):
                    tok = tok[len('{{l|en|'):-2]

                if not tok.startswith('{{'):
                    toks.append(tok)
            if toks:
                definitions.append(Markup(join(toks)))
    return definitions


def parse_list(lst):
    items = []
    for item in lst:
        if len(item) >= 3 and item[0] == '*':
            es = []
            for e in item[2:]:
                e = e.replace('\n', '')
                e = e.replace('----', '')
                if e.startswith('{{sense|'):
                    e = f"<i>({e[len('{{sense|'):-2]})</i>"
                    es.append(e)
                else:
                    if e.startswith('{{l|de|'):
                        e = e[len('{{l|de|'):-2]
                        if '|' in e:
                            e = e.split('|')[0]
                    if e.startswith('[['):
                        e = e[2:-2]
                        if '|' in e:
                            e = e.split('|')[1]
                    if not e.startswith('{{') and e:
                        e = link(e)
                        es.append(e)
            items.append(Markup(' '.join(es)))

    return items


def create_word_entry(word, pos, defs, synonyms, antonyms, related_words):
    first = defs[0]
    if pos == 'verb':
        if len(first) < 2 or not first[1].startswith('{{de-verb'):
            return None
        word = link(word)
        definitions = parse_definitions(defs[1:])
    elif pos == 'noun':
        if len(first) < 2 or not first[1].startswith('{{de-noun'):
            return None
        gender = first[1][2:-2].split('|')[1]
        articles = {
            'm': 'der',
            'n': 'das',
            'f': 'die',
            'p': 'die',
        }
        word = f'<i>{articles[gender]}</i> <span class="gender-{gender}">{link(word)}</span>'
        definitions = parse_definitions(defs[1:])
    elif pos == 'adjective':
        if len(first) < 2 or not first[1].startswith('{{de-adj'):
            return None
        word = link(word)
        definitions = parse_definitions(defs[1:])
    elif pos == 'adverb':
        if len(first) < 2 or not first[1].startswith('{{de-adv'):
            return None
        word = link(word)
        definitions = parse_definitions(defs[1:])
    else:
        assert False, pos

    if not definitions:
        return None

    entry = {
        'word': Markup(word),
        'definitions': definitions,
        'synonyms': parse_list(synonyms),
        'antonyms': parse_list(antonyms),
        'related_words': parse_list(related_words),
    }

    return entry


def load():
    words = load_words('data/words')
    for word in load_frequency('data/freqs'):
        if word in words:
            for pos, (defs, synonyms, antonyms,
                      related_words) in words[word][1]:
                entry = create_word_entry(word, pos, defs, synonyms, antonyms,
                                          related_words)
                if entry:
                    pos_to_words[pos].append(entry)


@app.route('/verbs')
def list_verbs():
    return render_template('words.html', words=pos_to_words['verb'])


@app.route('/nouns')
def list_nouns():
    return render_template('words.html', words=pos_to_words['noun'])


@app.route('/adverbs')
def list_adverbs():
    return render_template('words.html', words=pos_to_words['adverb'])


@app.route('/adjectives')
def list_adjectives():
    return render_template('words.html', words=pos_to_words['adjective'])


load()
