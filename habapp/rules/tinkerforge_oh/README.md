# tinkerforge openhab
python3 based daemon to handle changes in tinkerforge bricklets.

# Currently supported bricklets
* io16_2
  * derived:
  * io16_switch
  * io16_window

# currently implemented features
* configuration via [json file](tinkerforge_oh.json)
  * io16_2 (and all derived once)
    * configure callback timers for
      * complete bricklet
      * overwrite with specifc config for single ports
    * define OH-item for each port
  * io16_switch
    * detection of `long` and `short` press
  * trace configuration
* read OH items
* read map file to trace out the "correct" names
