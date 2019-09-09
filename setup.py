#!/usr/bin/env python

from setuptools import setup, find_packages
import os

# __version__ comes into namespace from here
with open(os.path.join("scribdl", "version.py")) as version_file:
    exec(version_file.read())

with open("README.rst", "r") as f:
    long_description = f.read()

setup(name='scribd-downloader',
      version=__version__,
      description='Download documents, books and audiobooks off Scribd',
      long_description=long_description,
      author='Ritiek Malhotra',
      author_email='ritiekmalhotra123@gmail.com',
      packages = find_packages(),
      entry_points={
            'console_scripts': [
                  'scribdl = scribdl.command_line:_command_line',
            ]
      },
      url='https://www.github.com/ritiek/scribd-downloader',
      keywords=['scribd-downloader', 'documents', 'command-line', 'python'],
      license='MIT',
      download_url='https://github.com/ritiek/scribd-downloader/archive/v' + __version__ + '.tar.gz',
      classifiers=[],
      install_requires=[
            'requests >= 2.19.1',
            'BeautifulSoup4 >= 4.6.3',
            'img2pdf >= 0.3.1',
            'md2pdf >= 0.4'
      ]
     )
