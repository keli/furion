Furion Socks5 SSL Proxy
=======================

Furion is an encrypted proxy written in Python. In essence, it's just
socks5 server with ssl support. It's often used with upstream Furion
servers to avoid censorship.

Project is hosted at `GitHub <https://github.com/keli/furion>`__,
mirrored on `BitBucket <https://bitbucket.org/keli/furion>`__.

Features
--------

-  Automatic upstream fail over (when multiple upstream servers are
   available).
-  Built-in latency check for choosing the fastest upstream.
-  Periodical upstream updates from a designated central registry.
-  Builtin DNS server/proxy to avoid poisoning.
-  Limit what ports that clients are allowed to connect to.
-  Easy account management on the server side.

Dependencies
------------

Furion has no external dependencies other than a standard Python 2.x
(>=2.6) installation. Python 3.x is supported. There is optional support
for gevent, which would be used if an existing gevent installation was
discovered.

Installation
------------

Furion can be installed via pip:

::

    pip install furion

or setuptools:

::

    easy_install furion

To start using Furion, you need at least a furion.cfg file. For client,
a upstream.json file is also needed for upstream checking to work.

By default, Furion will look for furion.cfg and upstream.json in ``/etc/furion``
or the current working directory. You can specify path to the configuration
file after a ``-c`` switch.

Read configuration files in
`examples <https://github.com/keli/furion/blob/master/examples>`__
directory for more information.

Client For Windows
~~~~~~~~~~~~~~~~~~

There is a win32 binary available for download with every
`release <https://github.com/keli/furion/releases>`__.

If you want to build yourself, a python installation must be present,
personally I used
`ActivePython <http://www.activestate.com/activepython>`__. Then install
`pyinstaller <http://www.pyinstaller.org>`__ to C:\\\\pyinstaller and
use
`pyinstaller.bat <https://github.com/keli/furion/blob/master/scripts/pyinstaller/pyinstaller.bat>`__
to build.
