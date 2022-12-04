# tinkerforge openhab
python3 based daemon to handle changes in tinkerforge bricklets.

# Currently supported bricklets
* BrickletIo16V2
  * derived:
    * BrickletIo16V2Switch
    * BrickletIo16V2Window

# currently implemented features
* configuration via [json file](tinkerforge_oh.json)
  * BrickletIo16V2 (and all derived once)
    * configure callback timers for
      * complete bricklet
      * overwrite with specifc config for single ports
    * define OH-item for each port
  * BrickletIo16V2Switch
    * detection of `long` and `short` press
  * trace configuration
* read OH items
* read map file to trace out the "correct" names
