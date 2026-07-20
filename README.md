
### PID-Analyzer 0.60 changes:
- Consolidated years of scattered fork fixes and dependency updates into one maintained branch (see "Changes in this fork" below)
- Modernized for current numpy/scipy/pandas/matplotlib; added PX4/ULog support; added bbl_parser as an alternative to blackbox_decode

### PID-Analyzer 0.52 changes:
- Fixed the noise plot ranges for better visual comparability with option for custom or auto range
- slight change to s/n in deconvolution: Gaussian instead of digital s/n

# PID-Analyzer

This program reads Betaflight blackbox logs and calculates the PID step response. It is made as a tool for a more systematic approach to PID tuning.

The step response is a characteristic measure for PID performance and often referred to in tuning techniques.
For more details read: https://en.wikipedia.org/wiki/PID_controller#Manual_tuning 
The program is Python based but utilizes blackbox_decode from Betaflight blackbox-log-viewer (https://github.com/betaflight/blackbox-log-viewer) to read logfiles,
or from iNavFlight blackbox-tools (https://github.com/iNavFlight/blackbox-tools), depending on your flight controller firmware. As an alternative to blackbox_decode,
[bbl_parser](https://github.com/nerdCopter/bbl_parser) is also supported - point `--blackbox_decode`/`config.ini` at whichever tool you have and it's auto-detected.
bbl_parser applies its own smart filtering to skip tiny/ground-test sessions by default; pass `--decoder-force-export` to include every session regardless. Use
`--decoder-type` to override auto-detection if it ever misidentifies your binary.

As an example: 
This was the BF 3.15 stock tune (including D Setpoint weight) on my 2.5" CS110: 
![stock tune](images/stock_tune.png)

This a nice tune I came up with after some testing: 
![good tune](images/good_tune.png)

You can even use angle mode, the result should be the same!
The program calculates the system response from input (PID loop input = What the quad should do) and output (Gyro = The quad does). 
Mathematically this is called deconvolution, which is the invers to convolution: Input * Response = Output. 
A 0.5s long response is calculated from a 1.5s long windowed region of interest. The window is shifted roughly 0.2s to calculate each next response. 
From a mathematical point of view this is necessary, but makes each momentary response correspond to an interval of roughly +-0.75s.
 
Any external input (by forced movement like wind) will result in an incomplete system and thus in a corrupted response. 
Based on RC-input and quality the momentary response functions are weighted to reduces the impact of corruptions. Due to statistics, more data (longer logs) will further improve reliability of the result. 

If D Setpoint Transition is set in Betaflight, your tune and thus the response will differ for high RC-inputs. 
This fact is respected by calculating separate responses for inputs above and below 500 deg/s. With just moderate input, you will get one result, if you also do flips there will be two.

Keep in mind that if you go crazy on the throttle it will cause more distortion.  If throttle-PID-attenuation (TPA) is set in Betaflight there will be a different response caused by a dynamically lower P. 
This is the reason why the throttle and TPA threshold is additionally plotted.

The whole thing is still under development and results/input of different and more experienced pilots will be appreciated!

## Requirements

### On debian-based distributions
To install required Python libraries, view the list of packages in `requirements.txt` or simply run:

```
sudo apt-get install python3-pip
sudo pip3 install -r requirements.txt
```

### On Arch Linux:
```
pacman -S python-matplotlib python-numpy python-scipy python-pandas
```

## How to use this program:
1. Record your log. Logs of 20s seem to give sufficient statistics. If it's slightly windy, longer logs can still give reasonable results. You can record multiple logs in one session: Each entry will yield a seperate plot.
2. Get a decoder: either `blackbox_decode` ([Betaflight blackbox-log-viewer](https://github.com/betaflight/blackbox-log-viewer) or [iNavFlight blackbox-tools](https://github.com/iNavFlight/blackbox-tools)) or [bbl_parser](https://github.com/nerdCopter/bbl_parser) — either is auto-detected (see above). Point PID-Analyzer at it via `config.ini` or `--blackbox_decode PATH`.
3. Run `python3 PID-Analyzer.py <log file(s)>` (or `./PID-Analyzer.py <log file(s)>` on Linux/macOS). Either pass your `.BBL`/`.BFL` file(s) directly as arguments, or omit them for an interactive prompt.
4. The logs are separated into temp files, read, analyzed, and a `.png` image is saved automatically in the folder corresponding to your entered name (default is `tmp`).

In case of problems, please report including the log file.

Tested on current Linux with Python 3.10+ and current numpy/scipy/pandas/matplotlib; should work on any platform with a working Python 3 + matplotlib install.

Happy tuning,

Flo

## Changes in this fork

* project restructured from monolithic into modular
* ability to load CSV exported from Blackbox Explorer
* refactored code to (more or less) follow Python conventions (WIP)
* add config file (`config.ini`) to set the path for `blackbox_decode` permanently
* use different default names for `blackbox_decode` executable on different platforms
* changed command-line usage syntax (see below)
* updated dependencies to floor versions (numpy, scipy, pandas, matplotlib), compatible
  with current releases
* fixed crashes on modern NumPy/Matplotlib (removed/changed APIs) and on low
  effective-rate logs
* equal noise-plot scaling across gyro/debug/D-term, and a warning when
  debug_mode doesn't expose prefiltered gyro data
* PX4/ULog (`.ulg`) log support, consolidated from across the fork ecosystem
  (deliphop, bw1129, bkueng - see git history for full attribution)
* tested on python 3.10+

### Usage

```bash
usage: PID-Analyzer.py [-h] [-n NAME] [--blackbox_decode PATH]
                       [--decoder-type {auto,blackbox_decode,bbl_parser}]
                       [--decoder-force-export] [-d] [-b NOISE_BOUNDS]
                       LOG_PATHS

positional arguments:
  LOG_PATHS             log file(s) to analyze or omit for interactive prompt

options:
  -h, --help            show this help message and exit
  -n, --name NAME       plot name (default: tmp)
  --blackbox_decode PATH
                        path to blackbox_decode or bbl_parser tool (default:
                        <repo-root>/blackbox_decode)
  --decoder-type {auto,blackbox_decode,bbl_parser}
                        override --blackbox_decode tool auto-detection
                        (default: auto)
  --decoder-force-export
                        bbl_parser only: bypass its smart session filtering
                        (--force-export) (default: False)
  -d, --hide            hide plot window when done (default: False)
  -b, --noise-bounds NOISE_BOUNDS
                        bounds of plots in noise analysis (use "auto" for
                        autoscaling) (default:
                        [[1.0,20.0],[1.0,20.0],[1.0,20.0],[0.0,4.0]])
```

## Installation in a virtual environment

Installing in a virtual environment means that the dependencies will be installed in a local directory instead of globally on the system. It's a less obtrusive method which may be preferred if you are not using the installed packages in other scripts or you need to have different versions of the same package for different scripts.

```
# create the virtual env in the working directory
python3 -m venv env
# activate the virtual env
. env/bin/activate
# optionally update package management tools
pip install -U pip wheel setuptools
# install dependencies locally
pip install -r requirements.txt
```

The above instructions is for Linux(-like) systems. For a more complete guide, please see the official [documentation for virtual environments](https://docs.python.org/3/library/venv.html).

