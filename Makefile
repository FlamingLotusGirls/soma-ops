OPC_SERVER_DIR=../soma/pier14/openpixelcontrol

all:
	$(MAKE) -C $(OPC_SERVER_DIR)

install: all
	install -p -o root -g root -m 755 $(OPC_SERVER_DIR)/soma_server	/usr/local/bin/soma-server
	install -p -o root -g root -m 755 bin/init.d-ubrain-clock	/etc/init.d/ubrain-clock
	install -p -o root -g root -m 755 bin/soma-scheduler		/usr/local/bin
	install -p -o root -g root -m 755 bin/ubrain-daemon		/usr/local/bin
	install -p -o root -g root -m 755 bin/ubrain-get-time		/usr/local/bin
	install -p -o root -g root -m 755 bin/launch-opc-client		/usr/local/bin
	install -p -o root -g root -m 755 bin/launch-opc-server		/usr/local/bin
	update-rc.d ubrain-clock defaults 1
