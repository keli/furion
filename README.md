Furion Socks5 SSL Proxy
=======================

Furion is an encrypted proxy written in Python. In essence, it's just socks5 server with ssl support. It's often used with upstream Furion servers to avoid censorship.

Features
--------

-   Automatic upstream fail over (when multiple upstream servers are available).
-   Built-in latency check for choosing the fastest upstream.
-   Periodical upstream updates from a designated central registry.
-   Builtin DNS server/proxy to avoid poisoning.
-   Limit what ports that clients are allowed to connect to.
-   Easy account management on the server side.

Dependencies
------------

Furion has no external dependencies other than a standard Python 3.x (>=3.8) installation. There is optional support for gevent, which would be used if an existing gevent installation was discovered.

Installation
------------

Furion can be installed via pip:

    pip install furion

or pipx

    pipx install furion

To start using Furion, you need at least a furion.cfg file.

By default, Furion will look for furion.cfg and upstream.json in `/etc/furion` or the current working directory. You can specify path to the configuration file after a `-c` switch.

For client, an upstream.json file is also needed for upstream checking to work in the same directory your furion.cfg resides in.

Alternatively, you can put the upstream.json file somewhere accessible via http(s), so that you can share that address with your friends. Then configure the `upstream` section of your `furion.cfg` file like below, to use that upstream file.

    [upstream]

    central_url = https://your.upstream.json

    autoupdate_upstream_list = on

    update_frequency = start

    upstream_list_path = upstream.json

Read configuration files in [examples](https://github.com/keli/furion/blob/master/examples) directory for more information.


### Building Standalone Windows Clients

* Install miniconda3
```
winget install miniconda3
```

* Create a new conda environment
```
conda create -n furion
```

* Activate the environment
```
conda activate furion
```

* Install pyinstaller
```
conda install -c conda-forge pyinstaller
```

* Install wxPython (optional if you only want to build the cli version)
```
conda install -c conda-forge wxpython
```

* Install furion itself
```
cd furion
pip install -e .
```

* Build the standalone client
```
cd scripts/pyinstaller
pyinstaller.bat
```

* The standalone clients will be in `dist/furion.exe` and `dist/furion-cli.exe`
* Furion.exe is only a tray icon currently.

Note: You need to put a config file `furion.cfg` in the same directory of the exe for it to work.
