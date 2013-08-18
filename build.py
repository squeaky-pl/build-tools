#!/usr/bin/env python


from os.path import (
    dirname, abspath, join, exists, normpath, basename, isabs)
from sys import platform
from xml.etree import ElementTree
from subprocess import check_call, check_output, Popen, PIPE
from os import chdir, makedirs
from textwrap import dedent


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
            for source in element.text.strip().splitlines():
                line = source.split()
                source = line[0]
                source_options = options.copy()
                source_options.update(dict.fromkeys(line[1:], True))

                patches = {}
                for subelement in element:
                    if subelement.tag == 'patch':
                        patches[subelement.attrib['to']] = (
                            dedent(subelement.text))

                install.append({
                    'patches': patches,
                    'source': source,
                    'options': source_options
                })

    return install


def first_component(archive):
    output = check_output(['tar', 'tf', archive])
    components = set(l.partition('/')[0] for l in output.splitlines())
    return components.pop()


here = dirname(abspath(__file__))


def execute_spec(install):
    from pdb import set_trace; set_trace()

    for spec in install:
        options = spec['options']
        dest = options.get('cd', here)
        source = spec['source']
        name = basename(source)
        dest_dir = join(here, dest)

        if isabs(dest_dir) and platform == 'win32':
            dest_dir = 'c:' + dest_dir

        if not exists(dest_dir):
            makedirs(dest_dir)

        dest = join(dest_dir, name)

        check_call(['wget', '-O', dest, source])
        check_call(['tar', 'xf', dest, '-C', dest_dir])

        archive_dir = join(dest_dir, first_component(dest))
        chdir(archive_dir)

        for path, stdin in spec['patches'].items():
            patch = Popen(['patch', path], stdin=PIPE)
            patch.communicate(stdin)

        configure = ['./configure']
        try:
            prefix = options.pop('prefix')
        except KeyError:
            pass
        else:
            prefix = join(here, prefix)
            configure.append('--prefix=' + prefix)

        configure.extend(k for k, v in options.items() if v is True)

        check_call(configure)
        check_call(['make', '-j4'])
        check_call(['make', 'install'])


def main():
    spec = find_spec()

    install = parse_spec(spec)

    execute_spec(install)

    return spec


if __name__ == '__main__':
    main()
