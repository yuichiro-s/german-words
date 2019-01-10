import sys
import json
import xml.etree.ElementTree as etree

import mwparserfromhell


def parse_definitions(section, numbered=False):
    items = []
    item = []
    if numbered:
        bullet = '#'
    else:
        bullet = '*'
    for node in section.nodes[1:]:
        if node.startswith('=='):
            break
        elif node == bullet and item:
            items.append(item)
            item = []
        item.append(node)
    if item:
        items.append(item)

    definitions = []
    for item in items:
        definition = []
        for node in item:
            definition.append(str(node))
        definitions.append(definition)

    return definitions


def parse_section(section):
    definitions = parse_definitions(section, numbered=True)
    synonyms = list(map(parse_definitions, section.get_sections(matches='Synonyms')))
    antonyms = list(map(parse_definitions, section.get_sections(matches='Antonyms')))
    related_terms = list(map(parse_definitions, section.get_sections(matches='Related terms')))
    return definitions, synonyms, antonyms, related_terms


def parse_sections(pos, sections):
    entries = []
    for section in sections:
        entries.append((pos, parse_section(section)))
    return entries


def main():
    title = None
    for _, elem in etree.iterparse(sys.stdin, events=['start']):
        if elem.tag.endswith('title'):
            title = elem.text
        elif elem.tag.endswith('text'):
            wikicode = mwparserfromhell.parse(elem.text)
            entries = []
            for section in wikicode.get_sections(matches='^German$'):
                entries.extend(parse_sections('adjective', section.get_sections(matches='Adjective')))
                entries.extend(parse_sections('verb', section.get_sections(matches='Verb')))
                entries.extend(parse_sections('adverb', section.get_sections(matches='Adverb')))
                entries.extend(parse_sections('noun', section.get_sections(matches='Noun')))
            if entries:
                obj = title, entries
                print(json.dumps(obj))
        elem.clear()


if __name__ == '__main__':
    main()
