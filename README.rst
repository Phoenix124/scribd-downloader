Scribd-Downloader
=================

|PyPi Version| |Build Status| |Coverage Status|

(I also found an online service https://dlscrib.com/ created by `Erik Fong`_. It doesn't
use this script as some people seem to think!).

Current features:

+------------+-------------------------------------+-------------------------------------------+
| Type       | Downloadable without Scribd premium | Requires Scribd premium for full download |
+============+=====================================+===========================================+
| Documents  |                 Yes                 |                    No                     |
+------------+-------------------------------------+-------------------------------------------+
| Books      |                 Yes                 |                    Yes                    |
+------------+-------------------------------------+-------------------------------------------+
| Audiobooks |                 Yes                 |                    Yes                    |
+------------+-------------------------------------+-------------------------------------------+

**Some information about Scribd documents:**

There are two types of documents on Scribd:

-  Documents made up using a collection of images and
-  Actual documents where the text can be selected, copied etc.

This script takes a different approach to both of them:

-  Documents consisting of a collection of images is straightforward and
   this script will simply download the induvidual images which can
   be combined to ``.pdf`` by passing ``--pdf`` option to the tool. Simple.

-  Actual documents where the text can be selected are hard to tackle.
   If we feed such a document to this tool, only the text present in
   document will be downloaded. Scribd seems to use javascript to somehow
   combine text and images. So far, I haven't been able to combine them
   with Python in a way they look like the original document.

------------
Installation
------------

Make sure you're using Python 3 (Python 2 is not supported by a few dependencies).
Then run these commands:

::

    $ pip install scribd-downloader

or install the development version with:

::

    $ python setup.py install

-----
Usage
-----

::

    usage: scribdl [-h] [-i] [-p] URL

    Download documents and books from scribd.com

    positional arguments:
      URL           scribd url to download

    optional arguments:
      -h, --help    show this help message and exit
      -i, --images  download url made up of images
      -p, --pdf     convert to pdf (*Nix: imagemagick)
      -c CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                            path to file containing your Scribd premium
                            credentials

--------
Examples
--------

Scribd Documents
----------------
Downloading text from document containing selectable text:
::
   $ scribdl https://www.scribd.com/document/55949937/33-Strategies-of-War

(Text will be saved side by side in a ``.md`` file in the current
working directory)

Download document containing images; use the ``--images`` option (the tool cannot figure out this on its own):
::
    $ scribdl -i https://scribd.com/doc/17142797/Case-in-Point

(Images will be saved in the current working directory)

Scribd Books
------------
The below command will generate an ``.md`` file of the book in the current working directory:
::
    $ scribdl https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room

Pass ``--pdf`` option to convert the generated output to a PDF.

This will only dowload the book content available without owning a premium account on Scribd.
See the below section for downloading full books if you own a premium Scribd account.

Scribd Audiobooks
-----------------
This will download .mp3 of the audiobook:
::
   $ scribdl https://www.scribd.com/audiobook/237606860/100-Ways-to-Motivate-Yourself-Change-Your-Life-Forever
   
This will only download the preview version of the audiobook. See the below section for
downloading complete audiobooks if you own a premium Scribd account.

-------------------------------------------------
Downloading complete textual books and audiobooks
-------------------------------------------------

If you have a premium Scribd account, you can also download the full version of
textual books and audiobooks.

Create a text file containing your Scribd credentials, such that the contents of the file look like below:
::
    user@mail.com
    password


Now pass the file path to the ``-c`` option, for example:
::
    $ scribdl -c scribd_credentials.txt https://www.scribd.com/audiobook/359295794/Principles-Life-and-Work

It should then download you all the audiobook chapters as mp3. Similarly, you could also download complete
contents of a Scribd book by replacing the URL with the URL of your choice.

If you're not willing to use place your account credentials in a file, you could also copy the cookie values
for ``_scribd_session`` and ``_scribd_expire`` when logged into your premium account on scribd on the web
browser and replace them with the ones in this file https://github.com/ritiek/scribd-downloader/blob/master/scribdl/const.py.

You should then be able to automatically download full version of both textual books and audiobooks
from Scribd using the tool by running the commands as usual.

----------
Disclaimer
----------

Downloading books from Scribd for free maybe prohibited. This tool is
meant for educational purposes only. Please support the authors by buying
their titles.

-------
License
-------

``The MIT License``

.. |PyPi Version| image:: https://img.shields.io/pypi/v/scribd-downloader.svg
   :target: https://pypi.org/project/scribd-downloader

.. |Build Status| image:: https://travis-ci.org/ritiek/scribd-downloader.svg?branch=master
   :target: https://travis-ci.org/ritiek/scribd-downloader

.. |Coverage Status| image:: https://codecov.io/gh/ritiek/scribd-downloader/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/ritiek/scribd-downloader

.. _Mitmproxy: https://github.com/mitmproxy/mitmproxy

.. _Erik Fong: mailto:dlscrib@gmail.com
.. _BookURL: https://www.scribd.com/read/189087235/Confessions-of-a-Casting-Director-Help-Actors-Land-Any-Role-with-Secrets-from-Inside-the-Audition-Room
.. ConstantValues:
