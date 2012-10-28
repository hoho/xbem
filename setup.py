import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="xbem-build",
    version="0.0.1",
    author="Marat Abdullin",
    author_email="dakota@brokenpipe.ru",
    description=("Build utility for XBEM files."),
    long_description=read("README.txt"),
    license="MIT",
    keywords="bem xbem build",
    url="http://xslc.org/xbem-build/",
    packages=["xbem_build"],
    scripts=["bin/xbem-build"],
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
