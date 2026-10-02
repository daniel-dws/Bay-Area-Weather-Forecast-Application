# Bay-Area-Weather-Forecast-Application

A Tkinter app for checking the 5-day weather forecast at Bay Area destinations. Pick one or more cities, and each one opens in its own window with daily highs, lows, wind speed, and UV index. Data comes from the [Open-Meteo](https://open-meteo.com/) API.

https://github.com/user-attachments/assets/85586488-86df-4e56-b2a2-25000c41eec3

## Features

- Select multiple destinations, grouped by region (North Bay, East Bay, Peninsula, South Bay, The Coast)
- 5-day forecast per city: high/low temperature (°F), wind speed (mph), and UV index
- Geocoding results are cached in `data.json`, so city coordinates are only requested once
- Save your results to `weather.txt` in a directory of your choice when you close the app

## Two versions

| File | Approach |
|---|---|
| `lab4thread.py` | Multithreading, with a producer-consumer queue so each forecast window opens as soon as its data arrives |
| `lab4process.py` | Multiprocessing, using a process pool for geocoding and a queue for weather results |

### Performance (seconds, 10 cities for geocoding)

| | Serial | Multithreading | Multiprocessing |
|---|---|---|---|
| Geocoding | 5.90 | 0.92 | 2.01 |
| Weather data | 5.88 | 0.94 | 1.48 |

Multithreading was fastest because the work is I/O bound, so threads spend most of their time waiting on the network. Multiprocessing still beat serial by running requests in parallel, but process startup and pickling data between processes add overhead that only pays off for CPU-bound work.

## Run it

Requires Python 3 and an internet connection.

```
pip install requests
python lab4thread.py
```

or

```
python lab4process.py
```

Keep `data.json` in the same folder as the script. If it's missing, the app recreates it. On Debian/Ubuntu you may also need `sudo apt install python3-tk`.

## Built with

Python, Tkinter, JSON, threading, multiprocessing, Open-Meteo APIs
