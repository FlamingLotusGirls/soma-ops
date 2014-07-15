#!/bin/bash

set -e
set -x

install -p -o root -g root -m 755 bin/init.d-ubrain-clock	/etc/init.d/ubrain-clock
install -p -o root -g root -m 755 bin/soma-scheduler		/usr/local/bin
install -p -o root -g root -m 755 bin/ubrain-daemon		/usr/local/bin
install -p -o root -g root -m 755 bin/ubrain-get-time		/usr/local/bin

update-rc.d ubrain-clock defaults 1
