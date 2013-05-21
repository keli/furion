Furion
======

Furion is an encrypted proxy written in Python. In essense, it's just a socks5 server with chaining and ssl support.

It's often used with a upstream Furion server to avoid censorship. 

**Notice**

Project moved to `GitHub <https://github.com/hukeli/furion>`_. 
But I'll do my best to maintain a mirror on `BitBucket <https://bitbucket.org/keli/furion>`_.
The download section on BB seems blocked in China though.

**Features**

* Automatic upstream failover (when multiple upstream servers are available) 
* Easy account management
* Prevents DNS leak by not allowing using IP address as
  destination in the protocol

**Dependencies**

Furion has no external dependencies other than a standard Python 2.x (>2.5) installation 

**How to use**

Read the configuration files in examples directory for more information.