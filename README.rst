Furion
======

Furion is an encrypted proxy written in Python. In essense, it's just socks5 client/server with chaining and ssl support.

It's often used with a upstream Furion server to avoid censorship. A few upstream servers are also included (see Installation_ section below), which can be used directly for people who just want to get things working ASAP. **DISCLAIMER BEGINS** I take absolutely no responsibilities for anything that happened to your data if you choose to use these upstream servers. **DISCLAIMER ENDS** With that being said, these upstream servers are assigned solely for this purpose and should be safe in general. So feel free to use them, but DO NOT ABUSE.  

Notice
------

Project moved to `GitHub <https://github.com/hukeli/furion>`_. 
But I'll do my best to maintain a mirror on `BitBucket <https://bitbucket.org/keli/furion>`_.
The download section on BB seems blocked in China though.

Features
--------

* Automatic upstream failover (when multiple upstream servers are available).
* Always use the fastest upstream with built-in latency check.
* Supports periodical upstream updates from a designated central registry. 
* Prevents DNS leak/poisoning.
* Limit what ports that clients are allowed to connect to.
* Easy account management on the server side.

Dependencies
------------

Furion has no external dependencies other than a standard Python 2.x (>2.5) installation 

Installation
------------

For Windows 
^^^^^^^^^^^^

There is a win32 binary available for download with every `release <https://github.com/hukeli/furion/releases>`_, configured as client for immediate use.

If you want to build yourself, a python installation must be present, personally I used `ActivePython <http://www.activestate.com/activepython>`_. Then install `pyinstaller <http://www.pyinstaller.org>`_ to `C:\\pyinstaller` and use `pyinstaller.bat <https://github.com/hukeli/furion/blob/master/pyinstaller/pyinstaller.bat>`_ to build.

Automated Installation
^^^^^^^^^^^^^^^^^^^^^^^

You can use `install.sh <https://github.com/hukeli/furion/blob/master/install.sh>`_ 
for quick installation on Mac or Linux (only tested on Debian for now):

- If you have git or hg on your system, you can download just the `install.sh` script::

	curl -O https://raw.github.com/hukeli/furion/master/install.sh

- ... Or if you don't, download the source zip file instead::

	curl -L -O https://github.com/hukeli/furion/archive/master.zip
	unzip master.zip
	cd furion-master

- Now run the script to install as a client::

	sudo bash install.sh client

- ... Or if you have your own VPS and want to install Furion as server on it::

	sudo bash install.sh server

The script will clone/copy the code to `/usr/local/furion`, copy appropriate `furion.cfg` from the examples directory, generate a new cert (if you chose to install as server), and try to run it as well as making it start at boot time. The same script can be run again in the future to upgrade to the latest master branch.

By default, when running as client Furion opens a socks5 proxy on `127.0.0.1:11080`, as a server `0.0.0.0:443`, unless you configured otherwise in `furion.cfg`.

Manual Installation
^^^^^^^^^^^^^^^^^^^^

If you can't use the installation script, manual installation is straight forward too. 

**TODO**

Read the script and configuration files in `examples <https://github.com/hukeli/furion/blob/master/examples>`_  directory for more information.


Use Cases
---------

Here are a few use cases that I have found personally:

SSH Proxy to bitbucket.org
^^^^^^^^^^^^^^^^^^^^^^^^^^

Bitbucket servers are sometimes blocked in China and I can't clone/commit via ssh.
Here is what I do on a Mac:

Install `connect <https://bitbucket.org/gotoh/connect/>`_ via `HomeBrew <http://mxcl.github.io/homebrew/>`_
(for Debian GNU/Linux user connect is also available as "connect-proxy")::

	brew intsall connect

Configure ssh to use "connect" and furion together for bitbucket::

	# Append to the end of .ssh/config
	Host bitbucket.org
	ProxyCommand connect -a none -S localhost:11080 %h %p

Now I can clone code via ssh from bitbucket without problem::

	hg clone ssh://hg@bitbucket.org/keli/furion

Automatically Use Furion to Visit Blocked Sites in Chrome
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Automatically Use Furion to Visit Blocked Sites in Firefox
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create A Secure HTTP Proxy with Polipo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build A Router That Transparently Redirect Selected Traffic via Furion with OpenWRT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^




