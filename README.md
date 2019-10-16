# onstar_component
This is an onstar component for Home-Assistant and Opel cars

Add this files to custom_components/ directory and configure like this:

```
sensor:
- platform: onstar_component
  username: !secret onstar_username
  password: !secret onstar_password
  pin:      !secret onstar_pin
  resources:
    - onstar.plate
    - onstar.laststatus
    - onstar.warningcount
    - onstar.errorcount
    - onstar.oillife
    - onstar.fuellevel
    - onstar.ignition
    - onstar.odometer
    - onstar.tirelf
    - onstar.tirelr
    - onstar.tirerf
    - onstar.tirerr
    - onstar.tirestatuslf
    - onstar.tirestatuslr
    - onstar.tirestatusrf
    - onstar.tirestatusrr
    - onstar.nextmainodo
    - onstar.nextmaindate
    - onstar.airbagok


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
