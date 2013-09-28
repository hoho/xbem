import os
from distutils.core import setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="xbem",
    version="0.1.3",
    author="Marat Abdullin",
    author_email="dakota@brokenpipe.ru",
    description=("Build utility for XBEM files."),
    long_description=read("README.md"),
    license="MIT",
    keywords="bem xbem build",
    url="http://xslc.org/XBEM",
    packages=["xbem", "xbem/tech"],
    scripts=["bin/xbem"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities"
    ]
)
