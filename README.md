# openHAB3-conf
config for the openHAB3 setup

## bindings
* bindings
  * Ambient Weather Binding
  * astro
  * homematic
  * hue
  * iCalendar
  * network
  * ntp
* Additions
  * Map transformation
  * InfluxDB Persistence
  * openHAB Cloud Connector

## additional SW
* openhabian-config
  * update/upgrade
  * Apply Improvements (10)
    * "can't be wrong" packages (11)
    * Bash&Vim (12)
    * System Tweaks (13)
    * Fix Permissions (14)
    * Samba (16)
  * Optional Components (20)
    * LogViewer (21)
    * Influx+Grafana (24)
      * see [How To proceed](https://community.openhab.org/t/13761/1)
    * Install HABApp (2C)
  * System Settings (30)
    * change hostname (31)
      * openhabianpi
    * set system locale
      * de_DE.UTF8
    * change passwords
  * openHAB related (40)
    * openHAB Release (41)
    * Remote Console (43)
  * Backup (50)
    * Backup (50)
    
* [phytonstatemachine](https://github.com/Rosi2143/python-statemachine)
  * system: pip install python-statemachine
  * openHAB: see [doc](https://github.com/Rosi2143/openHAB3-conf/tree/master/automation/lib/python/personal) 
* tinkerforge
  * [brickd](https://www.tinkerforge.com/de/doc/Software/Brickd_Install_Linux.html#brickd-install-linux)
  * [brick-flash](https://www.tinkerforge.com/de/doc/Software/Brickd_Install_Linux.html#brickd-install-linux)
  * [python binding](https://www.tinkerforge.com/de/doc/Software/API_Bindings_Python.html#api-bindings-python)

## copying git repos
* create ssh-key
* copy conf
  * cd /etc
  * sudo mv openhab openhab_org
  * sudo mkdir openhab
  * sudo chown openhab openhab
  * sudo chgrp openhab openhab
  * sudo chmod g+w openhab
  * git clone git@github.com:Rosi2143/openHAB3-conf.git openhab
  * cd openhab
  * sudo chown -R openhab .
* copy user
  * cd /var/lib
  * same as for `conf`

## other configs
* mount USB-Stick
  * https://raspberrytips.com/mount-usb-drive-raspberry-pi/
* change log directory to USB 
* add aliases:
  * cdgitconf:
  * cdgituser: 
