# set logging level
log:set DEBUG jsr223.jython

# requirements statemachines
## installed package

https://pypi.org/project/python-statemachine/ via

### minimum version 1.0.3
* `sudo -u openhab pip install --ignore-installed --target=$OPENHAB_CONF/automation/lib/python/personal python-statemachine`
* `/home/openhabian/.local/bin/pip2 install --ignore-installed --target=$OPENHAB_CONF/automation/lib/python/personal typing`
* `/home/openhabian/.local/bin/pip2 install --ignore-installed --target=$OPENHAB_CONF/automation/lib/python/personal pydot`
