Furion
======

Furion is an encrypted proxy written in Python. In essense, it's just a socks5 server with chaining and ssl support.

It's often used with a upstream Furion server to avoid censorship. 

Notice
------

Project moved to `GitHub <https://github.com/hukeli/furion>`_. 
But I'll do my best to maintain a mirror on `BitBucket <https://bitbucket.org/keli/furion>`_.
The download section on BB seems blocked in China though.

Features
--------

* Automatic upstream failover (when multiple upstream servers are available).
* Easy account management.
* Prevents DNS leak/poisoning.
* Limit what ports that clients are allowed to connect to.

Dependencies
------------

Furion has no external dependencies other than a standard Python 2.x (>2.5) installation 

How to use
----------

You can use `install.sh <https://githug.com/hukeli/furion/blob/master/install.sh>`_ 
for quick installation on Linux/Mac::

	curl -O https://raw.github.com/hukeli/furion/master/install.sh
	sudo bash install.sh client
	# Or if you have your own VPS and want to install Furion as server on it
	sudo bash install.sh server

I've included a few upstream servers which can be used directly 
for people who just want to get things working ASAP. 
They are just tiny VPS instances, DO NOT ABUSE and force me to shut them down.

When running as client Furion opens a socks5 proxy on localhost:11080.

Read the script and configuration files in examples directory for more information.

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




