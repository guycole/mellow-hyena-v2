# mellow-hyena-v2
Aviation ADSB and UAT collection application.

## Introduction
A Mellow Hyena collector observes aviation beacons such as ADSB and UAT and shares the observation w/a backend for storage and reporting.

Mellow Hyena collectors are hosted on either Raspberry Pi or Odroid C4 hosts using RTL-SDR dongles.  

ADSB collectors frequently have a dedicated external antenna while UAT collectors share a multicoupler.

Each observation produces a single JSON output file which captures the current state.  The "observations" are beacons collected via RTL-SDR and "adsbex" contains amplifying information from ADSB exchange.

## Sample JSON output
```
{
    "equipment": {
        "antenna": "coaxial collinear",
        "receiver_id": 10,
        "receiver_type": "rtl-sdr-v3",
        "platform": "rpi4",
        "hostName": "pi4k"
    },
    "geoLoc": {
        "altitude": MSL in meters
        "latitude": +north decimal degress
        "longitude": +east decimal degrees
        "site": site name
    },
    "timeStamp": {
        "epochSeconds": collection time in seconds since epoch
        "iso8601": epochSeconds as a ISO8601 string
    },
    "crate": crate name
    "fileName": file name
    "mode": dump1090 for ADSB, dump978 for UAT
    "project": source project (hyena-v2)
    "version": schema version
    "adsbex": {
        "c05f09": {
            "adsb_hex": "c05f09",
            "category": "A3",
            "emergency": "none",
            "flight": "JZA597",
            "registration": "C-GJZS",
            "model": "CRJ9",
            "ladd_flag": false,
            "military_flag": false,
            "pia_flag": false,
            "wierdo_flag": false
        },
        "a2ed5a": {
            "adsb_hex": "a2ed5a",
            "category": "A3",
            "emergency": "none",
            "flight": "SKW3897",
            "registration": "N288SY",
            "model": "E75L",
            "ladd_flag": false,
            "military_flag": false,
            "pia_flag": false,
            "wierdo_flag": false
        }
    },
    "observations": [
        {
            "hex": "c05f09",
            "flight": "JZA597",
            "latitude": "40.386017",
            "longitude": "-122.238281",
            "altitude": "33000",
            "track": "0",
            "speed": "434"
        },
        {
            "hex": "a2ed5a",
            "flight": "SKW3897",
            "latitude": "40.561203",
            "longitude": "-122.064941",
            "altitude": "34000",
            "track": "1",
            "speed": "419"
        }
    ]
}
```