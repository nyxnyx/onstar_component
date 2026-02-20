---
marp: true
theme: default
paginate: true
backgroundColor: #121212
color: #e0e0e0
style: |
  section {
    font-family: 'Inter', sans-serif;
  }
  h1 {
    color: #448aff;
  }
  h2 {
    color: #82b1ff;
  }
  footer {
    color: #666;
  }
---

# Opel OnStar for Home Assistant
### Smart Vehicle Integration
**by Grzegorz Szostak (nyxnyx)**

![bg right:40% 80%](./onstar_ha_cover.png)

---

## The Vision
Bringing Opel/Vauxhall vehicles into the modern smart home ecosystem.

- **Unified Dashboard**: View car stats alongside home devices.
- **Automation Ready**: Trigger home actions based on car location or status.
- **Maintenance Tracking**: Never miss an oil change or tire pressure warning.

---

## Key Features

- 📍 **GPS Tracking**: Real-time location with `device_tracker`.
- ⛽ **Telemetry**: Fuel level, range, and odometer readings.
- 🔧 **Diagnostics**: Oil life, tire pressure (all 4 tires), and airbag status.
- 🕒 **Last Update**: Transparent status of when the data was last fetched.
- 🔒 **Secure**: Encrypted credential handling via Home Assistant secrets.

---

## Technical Architecture

Built for performance and reliability:

1. **Python OnStar SDK**: Direct communication with GM/OnStar API.
2. **Asynchronous I/O**: Non-blocking updates to keep Home Assistant responsive.
3. **Throttling Logic**: Optimized API calls to prevent account lockout.
4. **Custom Component Design**: Follows HACS-compatible structure.

---

## Integration Overview

```yaml
# configuration.yaml example
onstar_component:
  username: YOUR_USERNAME
  password: YOUR_PASSWORD
  pin: YOUR_PIN
```

- **Sensors**: Dozens of diagnostic entities.
- **Device Tracker**: Integrated car position.
- **Service**: Manual `update_state` trigger available.

---

## Current Status & Roadmap

### Current Focus
- [x] Core sensor implementation.
- [x] Robust error handling.
- [x] Test suite coverage.

### Next Steps 🚀
- [ ] Support for multiple vehicles.
- [ ] Climate control integration (Pre-conditioning).
- [ ] Door lock/unlock services.

---

## Q&A
### Thank You!

**Repository:** `nyxnyx/onstar_component`
**Contact:** szostak.grzegorz@gmail.com
