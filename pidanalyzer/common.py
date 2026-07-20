import configparser
import logging
import os
import platform
import subprocess

CONFIG_FILE = "config.ini"
BLACKBOX_DECODE_PATH = None
DECODER_TYPE = None
DECODER_FORCE_EXPORT = False
DEFAULT_NOISE_BOUNDS = [[1., 20.], [1., 20.], [1., 20.], [0., 4.]]
# different versions of fw have different names for the same thing.
FIELDS_MAP = {'dynThrPID': 'dynThrottle',
              'Craft name': 'craftName',
              'Firmware type': 'fwType',
              'Firmware revision': 'version',
              'Firmware date': 'fwDate',
              'rcRate': 'rcRate', 'rc_rate': 'rcRate',
              'rcExpo': 'rcExpo', 'rc_expo': 'rcExpo',
              'rcYawExpo': 'rcYawExpo', 'rc_expo_yaw': 'rcYawExpo',
              'rcYawRate': 'rcYawRate', 'rc_rate_yaw': 'rcYawRate',
              'rates': 'rates',
              'rollPID': 'rollPID',
              'pitchPID': 'pitchPID',
              'yawPID': 'yawPID',
              ' deadband': 'deadBand',
              'yaw_deadband': 'yawDeadBand',
              'tpa_breakpoint': 'tpa_breakpoint',
              'minthrottle': 'minThrottle',
              'maxthrottle': 'maxThrottle',
              'dtermSetpointWeight': 'dTermSetPoint', 'dterm_setpoint_weight': 'dTermSetPoint',
              'vbat_pid_compensation': 'vbatComp', 'vbat_pid_gain': 'vbatComp',
              'gyro_lpf': 'gyro_lpf',
              'gyro_lowpass_type': 'gyro_lowpass_type',
              'gyro_lowpass_hz': 'gyro_lowpass_hz', 'gyro_lpf_hz': 'gyro_lowpass_hz',
              'gyro_notch_hz': 'gyro_notch_hz',
              'gyro_notch_cutoff': 'gyro_notch_cutoff',
              'dterm_filter_type': 'dterm_filter_type',
              'dterm_lpf_hz': 'dterm_lpf_hz',
              'yaw_lpf_hz': 'yaw_lpf_hz',
              'dterm_notch_hz': 'dterm_notch_hz',
              'dterm_notch_cutoff': 'dterm_notch_cutoff',
              'debug_mode': 'debug_mode',
              }
# string fragment for identifying the main fields header row in CSV file
CSV_HEADER_ROW_FRAGMENT = "loopIteration"

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)
log = logging.getLogger()


def strip_quotes(filepath: str) -> str:
    return filepath.strip().strip("'").strip('"')


def clean_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(strip_quotes(path)))


def get_blackbox_decode_path() -> str:
    cwd = os.path.dirname(os.path.dirname(__file__))
    config_file_path = os.path.join(cwd, CONFIG_FILE)
    if not os.path.exists(config_file_path):
        system = platform.system()
        if system == 'Windows':
            executable = 'Blackbox_decode.exe'
        else:
            executable = 'blackbox_decode'
        return os.path.join(cwd, executable)
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config['paths']['blackbox_decode']


def detect_decoder_type(path: str) -> str:
    # bbl_parser (https://github.com/nerdCopter/bbl_parser) always prints a
    # 'bbl_parser X.Y.Z ...' banner; blackbox_decode has no --version flag at
    # all, so any probe failure/timeout/unexpected output means blackbox_decode.
    try:
        result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
        if result.stdout.startswith('bbl_parser '):
            return 'bbl_parser'
    except (OSError, subprocess.SubprocessError):
        pass
    return 'blackbox_decode'


def headerdict(log_file: str, log_number: int = 0) -> dict:
    # in case info is not provided by log, empty str is printed in plot
    return {'tempFile': log_file, 'dynThrottle': '', 'craftName': '', 'fwType': '', 'version': '', 'date': '',
            'rcRate': '', 'rcExpo': '', 'rcYawExpo': '', 'rcYawRate': '', 'rates': '', 'rollPID': '',
            'pitchPID': '', 'yawPID': '', 'deadBand': '', 'yawDeadBand': '', 'logNum': str(log_number),
            'tpa_breakpoint': '0', 'minThrottle': '', 'maxThrottle': '', 'tpa_percent': '',
            'dTermSetPoint': '', 'vbatComp': '', 'gyro_lpf': '', 'gyro_lowpass_type': '',
            'gyro_lowpass_hz': '', 'gyro_notch_hz': '', 'gyro_notch_cutoff': '', 'dterm_filter_type': '',
            'dterm_lpf_hz': '', 'yaw_lpf_hz': '', 'dterm_notch_hz': '', 'dterm_notch_cutoff': '',
            'debug_mode': ''}
