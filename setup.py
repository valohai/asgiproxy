import re

import setuptools

with open('./asgiproxy/__init__.py', 'r') as infp:
    version = re.search("__version__ = ['\"]([^'\"]+)['\"]", infp.read()).group(1)

try:
    with open('./requirements-dev.in', 'r') as infp:
        dev_dependencies = [l for l in infp if not l.startswith('-r')]
except IOError:
    dev_dependencies = []

if __name__ == '__main__':
    setuptools.setup(
        name='asgiproxy',
        version=version,
        url='https://github.com/valohai/asgiproxy',
        author='Valohai',
        author_email='dev@valohai.com',
        maintainer='Aarni Koskela',
        maintainer_email='akx@iki.fi',
        license='MIT',
        install_requires=['aiohttp', 'starlette', 'websockets'],
        tests_require=dev_dependencies,
        extras_require={'dev': dev_dependencies},
        packages=setuptools.find_packages('.', exclude=('tests',)),
        include_package_data=True,
    )
