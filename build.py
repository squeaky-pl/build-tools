#!/usr/bin/env python


from os.path import dirname, abspath, join, exists, normpath, basename
from xml.etree import ElementTree
from subprocess import check_call, check_output
from os import chdir


def find_spec():
    current = dirname(abspath(__file__))

    while 1:
        spec = join(current, 'build.spec.xml')
        if exists(spec):
            return spec

        if current == '/':
            break

        current = normpath(join(current, '..'))


def parse_spec(spec):
    install = []
    options = {}

    root = ElementTree.parse(spec).getroot()

    for element in root:
        if element.tag == 'options':
            content = element.text.split()
            options.update(dict(zip(content[::2], content[1::2])))
        if element.tag == 'install':
            sources = element.text.split()

            for source in sources:
                install.append({
                    'source': source,
                    'options': options.copy()
                })

    return install


def first_component(archive):
    output = check_output(['tar', 'tf', archive])
    components = set(l.partition('/')[0] for l in output.splitlines())
    return components.pop()


here = dirname(abspath(__file__))


def execute_spec(install):
    for spec in install:
        options = spec['options']
        dest = options.get('cd', here)
        source = spec['source']
        name = basename(source)
        dest_dir = join(here, dest)
        dest = join(dest_dir, name)

        check_call(['wget', '-O', dest, source])
        check_call(['tar', 'xf', dest, '-C', dest_dir])

        archive_dir = join(dest_dir, first_component(dest))
        chdir(archive_dir)
        check_call(['./configure'])
        check_call(['make', '-j4'])


def main():
    spec = find_spec()

    install = parse_spec(spec)

    execute_spec(install)

    return spec


if __name__ == '__main__':
    main()
