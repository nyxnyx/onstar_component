# onstar_component
This is an onstar component for Home-Assistant and Opel cars

There was change from initial version. Now it has sensor and device_tracker.

CHANGE your config if you were using it without device_tracker!!!!

Now sensor is detected automatically. So first if you have defined sensor - remove it.

Add this files to custom_components/ directory and configure:

```
onstar_component:
  username: !secret onstar_username
  password: !secret onstar_password
  pin:      !secret onstar_pin
```

After restart of HA you will see sensor.onstar.\* 


Example setup for lovelace cards:

```
title: Opel Insignia
path: opel
icon: mdi:car 

cards:
  - type: entities
    entities:
    - sensor.onstar_plate
    - sensor.onstar_laststatus
    - sensor.onstar_fuellevel
    - sensor.onstar_oillife
    - sensor.onstar_nextmaindate
    - sensor.onstar_nextmainodo
    - sensor.onstar_tirelf
    - sensor.onstar_tirerf
    - sensor.onstar_tirelr
    - sensor.onstar_tirerr
```

device_tracker will show new device with your license plate set as name and icon being a car. Look for it on the map :)

Current list of sensors:
- onstar.plate - Plate
- onstar.laststatus - Last updated
- onstar.warningcount - Warnings
- onstar.errorcount - Errors
- onstar.oillife - Oil life
- onstar.fuellevel - Fuel level
- onstar.ignition - Ignition
- onstar.odometer - Odometer
- onstar.tirelf - Left Front Tyre
- onstar.tirelr - Left Rear Tyre
- onstar.tirerf - Right Front Tyre
- onstar.tirerr - Right Rear Tyre
- onstar.tirestatuslf - Left Front Tyre Status
- onstar.tirestatuslr - Left Rear Tyre Status
- onstar.tirestatusrf - Right Front Tyre Status
- onstar.tirestatusrr - Right Rear Tyre Status
- onstar.nextmainodo - Next maintenance
- onstar.nextmaindate - Next maintenance Date
- onstar.airbagok - Airbag status
- onstar.localisation - Latest localisation
- onstar.vin - VIN
