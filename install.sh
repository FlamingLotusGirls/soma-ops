#!/bin/bash

set -e
set -x

SOMADIR=../soma/pier14/openpixelcontrol

make -C$SOMADIR
install -p -o root -g root -m 755 $SOMADIR/soma_server		/usr/local/bin
install -p -o root -g root -m 755 bin/init.d-ubrain-clock	/etc/init.d/ubrain-clock
install -p -o root -g root -m 755 bin/soma-scheduler		/usr/local/bin
install -p -o root -g root -m 755 bin/ubrain-daemon		/usr/local/bin
install -p -o root -g root -m 755 bin/ubrain-get-time		/usr/local/bin

update-rc.d ubrain-clock defaults 1
