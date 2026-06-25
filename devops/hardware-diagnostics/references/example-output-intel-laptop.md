# Example: Full Hardware Diagnostic Output

From a session on Intel i7-8550U laptop with Samsung 960 EVO (NVMe) + SAMSUNG MZ7L3960 (SATA), 2026-06-07.

## SMART — NVMe System Disk (Healthy)

```
critical_warning              : 0
available_spare               : 100%
percentage_used               : 0%
media_errors                  : 0
temperature                   : 52°C
power_on_hours                : 21
unsafe_shutdowns              : 91
```

## SMART — SATA Backup Disk (Healthy)

```
SMART overall-health self-assessment test result: PASSED
Reallocated_Sector_Ct         : 0
Uncorrectable_Error_Cnt       : 0
CRC_Error_Count               : 0
Wear_Leveling_Count           : 9
Temperature_Celsius           : 59°C
Power_On_Hours                : 1704
```

## Sensors Output

```
iwlwifi_1:        +65.0°C
nvme Composite:   +51.9°C (high=76.8°C, crit=78.8°C)
nvme Sensor 2:    +61.9°C
CPU Package:      +78.0°C (high=100°C, crit=100°C)
Core 0:           +75.0°C
Core 1:           +72.0°C
Core 2:           +78.0°C
Core 3:           +73.0°C
PCH Skylake:      +63.5°C
```

## Thermal Zones (/sys)

```
pch_skylake: 63.5°C
iwlwifi_1:   68.0°C
x86_pkg_temp:78.0°C
```

## Cooling Devices

```
Processor (×8):     state=0/3        (not throttling)
intel_powerclamp:   state=0/100      (not active)
TCC Offset:         state=5/63       (throttling starts at Tjmax-5°C)
```

## dmesg

No disk/IO errors. Only PCIe correctable errors from iwlwifi (WiFi card) — harmless.

## Filesystem Check

```
exfat /dev/sda2:        clean. directories 3114, files 24680
ext4 /:                 Filesystem state: clean
ext4 /boot:             Filesystem state: clean
```

## Notes

- Fan speed and voltage sensors absent — typical for this laptop platform (EC not exposed to lm-sensors)
- GPU temp not separately available — Intel UHD 620 uses CPU package temp as proxy
- CPU at 78°C under moderate load — normal for 15W U-series in a laptop chassis
- TCC Offset=5 means throttling would begin at 95°C (100-5), well above current temp
