- [openHAB3-conf](#openhab3-conf)
  - [bindings](#bindings)
  - [additional SW](#additional-sw)
  - [copying git repos](#copying-git-repos)
  - [other configs](#other-configs)
- [Update 4.x](#update-4x)

# openHAB3-conf
config for the openHAB3 setup

## bindings
* bindings
  * Ambient Weather Binding
  * astro
  * bosch indego
  * home connect
  * homematic
  * hue
  * iCalendar
  * network
  * ntp
* Additions
  * Map Transformation
  * JSONPath Transformation
  * RegEx Transformation
  * Javascript Transformation
  * InfluxDB Persistence
  * openHAB Cloud Connector
* Automation
  * Groovy Scripting
  * JavaScript Scripting
  * Jython Scripting

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
  * system: see [Readme](.\habapp\README.md)
  * openHAB: see [doc](https://github.com/Rosi2143/openHAB3-conf/tree/master/automation/lib/python/personal)
* tinkerforge
  * [brickd](https://www.tinkerforge.com/de/doc/Software/Brickd_Install_Linux.html#brickd-install-linux)
  * [brick-flash](https://www.tinkerforge.com/de/doc/Software/Brickd_Install_Linux.html#brickd-install-linux)
  * [python binding](https://www.tinkerforge.com/de/doc/Software/API_Bindings_Python.html#api-bindings-python)

## copying git repos
* create ssh-key
* install graphviz
  * sudo apt install graphviz
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
  * add new location to samba
    * `sudo nano /etc/samba/smb.conf`
    *
        ```
          [openHAB-USB]
          comment=USBDrive
          path=/mnt/usb1
          writeable=yes
          public=no
          create mask=0664
          directory mask=0775
          veto files = /Thumbs.db/.DS_Store/._.DS_Store/.apdisk/._*/
          delete veto files = yes
        ```

  * allow OH to write logs
    * `sudo chmod -R g+w /mnt/usb1/log/`
    * `sudo chgrp -R openhab /mnt/usb1/log/`
    * `sudo chown -r openhab /mnt/usb1/log/`
  * change log location
    * `sudo systemctl edit openhab.service`
        ```
        [Service]
        Environment=OPENHAB_LOGDIR=
        Environment=OPENHAB_LOGDIR=/mnt/usb1/log/openhab
        ```
  * change logViewer
    * `sudo systemctl edit frontail.service`
        ```
        [Service]
        ExecStart=
        ExecStart=/usr/lib/node_modules/frontail/bin/frontail --disable-usage-stats --ui-highlight --ui-highlight-preset /usr/lib/node_modules/frontail/preset/openhab_AEM.json --theme openhab_AEM --lines 2000 --number 200 /mnt/usb1/log/openhab/openhab.log /mnt/usb1/log/openhab/events.log

        ```

    * restart openhab
* change log directory to USB
* add aliases:
  * `vi ~/.bash_aliases`
  * `alias cdgitconf='cd $OPENHAB_CONF'`
  * `alias cdgituser='cd $OPENHAB_USER'`
* clone "public files"
  * `mkdir ~/git`
  * `cd ~/git`
  * `git clone git@github.com:Rosi2143/public_files.git`
* create passwordless access to karaf
  * enable command execution from HabApp without passwords
  * see
    * https://karaf.apache.org/manual/latest/security#:~:text=For%20the%20SSH%20layer%2C%20Karaf,Karaf%20SSHD%20(server%20side).
    * https://openhabforum.de/viewtopic.php?t=5609
  * create key file `karaf.id_rsa`
  * copy key files to `/home/openhab/.ssh/`
  * change permissions
    ```
    sudo chgrp openhab /home/openhab
    sudo chgrp openhab /home/openhab/.ssh
    sudo chgrp openhab /home/openhab/.ssh/karaf.id_rsa
    sudo chgrp openhab /home/openhab/.ssh/karaf.id_rsa.pub

    sudo chown openhab /home/openhab
    sudo chown openhab /home/openhab/.ssh
    sudo chown openhab /home/openhab/.ssh/karaf.id_rsa
    sudo chown openhab /home/openhab/.ssh/karaf.id_rsa.pub
    ```

# Update 4.x
* [release note](https://www.openhab.org/blog/2023-07-23-openhab-4-0-release.html)

