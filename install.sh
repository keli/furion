#!/bin/bash

# Exit on error
set -e

INSTALL_PATH=/usr/local/furion

function check_sanity {
	if [[ $(id -u) != "0" ]]; then
		die 'Must be run by root user'
	fi
	if [[ -z `which python` ]]; then
		die "Cannot find python"
	fi
}

function die {
	echo "ERROR:" $1 > /dev/null 1>&2
	exit 1
}

function print_info {
	echo -n -e '\e[1;36m'
	echo -n $1
	echo -e '\e[0m'
}

function usage {
	cat << EOF 
Usage:
$0 client # install furion as a client (use upstream servers as proxies) 
$0 server # install furion as a server (acting as an upstream proxy server) 
EOF
	exit
}

function download {
	GIT=`which git`
	HG=`which hg`

	if [[ -n $GIT ]]; then
		git clone https://github.com/hukeli/furion.git $INSTALL_PATH
	elif [[ -n $HG ]]; then
		hg clone https://bitbucket.org/keli/furion $INSTALL_PATH
	else
		die "Can't find git or hg in your system, install one of them first."
	fi
}

function prepare_server {
	cd $INSTALL_PATH
	cp examples/furion_server.cfg furion.cfg
	cp examples/simpleauth.passwd .

	openssl req \
		-x509 -nodes -days 365 \
		-subj "/C=US/ST=CA/L=LA/CN=$1.com" \
		-newkey rsa:1024 -keyout furion.pem -out furion.pem
}

function prepare_client {
	cd $INSTALL_PATH
	cp examples/furion_client.cfg .
}

function install {
	check_sanity
	case $OSTYPE in
		darwin*)
			download
			prepare_$1 `date | md5 | head -c 10`
			cp -f examples/hu.keli.furion.plist /Library/LaunchDaemons/
			launchctl load /Library/LaunchDaemons/hu.keli.furion.plist
			;;	
		linux*)
			if [ ! -f /etc/debian_version ]; then
				die "The script supports only Debian for now."
			fi
			download
			prepare_$1 `date | md5sum | head -c 10`
			cp -f examples/furion.init /etc/init.d/furion
			update-rc.d furion defaults
			service furion start
			;;
	esac		
}

[[ $# < 1 ]] && usage

case $1 in
	client|server)
		install $1
		;;
	*)
		usage
		;;
esac
