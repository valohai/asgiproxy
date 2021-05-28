import re

import setuptools


def read_dependencies(filename):
    with open(filename, "r") as infp:
        return [l for l in infp if not l.startswith("-r")]


with open("./asgiproxy/__init__.py", "r") as infp:
    version = re.search("__version__ = ['\"]([^'\"]+)['\"]", infp.read()).group(1)

dependencies = read_dependencies("./requirements.in")

try:
    dev_dependencies = read_dependencies("./requirements-dev.in")
except IOError:
    dev_dependencies = []

if __name__ == "__main__":
    setuptools.setup(
        name="asgiproxy",
        version=version,
        url="https://github.com/valohai/asgiproxy",
        author="Valohai",
        author_email="dev@valohai.com",
        maintainer="Aarni Koskela",
        maintainer_email="akx@iki.fi",
        license="MIT",
        install_requires=dependencies,
        tests_require=dev_dependencies,
        extras_require={"dev": dev_dependencies},
        packages=setuptools.find_packages(".", exclude=("tests",)),
        include_package_data=True,
    )
