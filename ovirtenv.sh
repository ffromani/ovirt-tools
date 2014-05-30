#!/bin/bash

# defaults
OVIRT_ROOT="/srv/virtstore/engine"

# try config file
if [ -f "$HOME/.ovirtenvrc" ]; then
	. $HOME/.ovirtenvrc
fi

function ovirtls()
{
	echo "oVirt engine root is: $OVIRT_ROOT"
	if [ -d "$OVIRT_ROOT" ]; then
		echo "oVirt engines:"
		for item in $(ls $OVIRT_ROOT); do
			if [ -x "$OVIRT_ROOT/$item/bin/engine-setup" ]; then
				echo -n " $item"
			fi
		done
	else
		echo "no engines available."
	fi
}

function ovirton()
{
	if [ -z "$1" ]; then
		echo "missing oVirt env"
	elif [ ! -x "$OVIRT_ROOT/$1/$bin/engine-setup" ]; then
		echo "invalid oVirt env: {$1}"
	else
		export OVIRT_ENV="$1"
		export OLD_PS1="$PS1"
		export PS1="{$1}$PS1"
	fi
}

function ovirtoff()
{
	if [ -z "$OVIRT_ENV" ]; then
		echo "not into an oVirt env (use ovirton)"
	else
		export PS1="$OLD_PS1"
		unset OLD_PS1
		unset OVIRT_ENV
	fi
}

function ovirtstart()
{
	if [ -z "$OVIRT_ENV" ]; then
		echo "not into an oVirt env (use ovirton)"
	else
		cd "$OVIRT_ENV/bin"
		./ovirt-engine.py start
	fi
}

function ovirtcd()
{
	if [ -z "$OVIRT_ENV" ]; then
		echo "not into an oVirt env (use ovirton)"
	else
		cd "$OVIRT_ENV"
	fi
}

function ovirtdb()
{
	echo "not yet implemented"
}
