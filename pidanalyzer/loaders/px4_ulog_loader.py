from typing import Tuple

import numpy as np
from scipy.interpolate import interp1d

from .loader import Loader
from ..common import *

LOG_EXTENSIONS = [".ulg"]

# PX4 topics don't share a common timeline; interp1d needs extrapolation to cover
# the ends of sensor_combined's time range.
_RESAMPLE_KWARGS = {'fill_value': 'extrapolate'}


class Px4UlogLoader(Loader):
    """Loads PX4 ULog flight logs.

    PX4 supplies the rate setpoint directly (no p_err/P to derive it from, unlike
    Betaflight) and carries no D-term/debug traces, so only the response plot is
    produced - see Trace.has_noise_data / plotting.show_plots.
    """

    @staticmethod
    def is_applicable(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in LOG_EXTENSIONS

    def _read_headers(self, path: str) -> Tuple[dict]:
        base, _ = os.path.splitext(path)
        # response/noise figures build their output filename via `path[:-13]`;
        # this placeholder tail is exactly 13 chars so that slice lands on `base_`
        temp_file = base + "_temp0.01.ulog"
        headers = headerdict(temp_file)
        # tpa_percent must be numeric (used directly in a plt.hlines call); the
        # rest stay as headerdict()'s empty-string BF-metadata defaults.
        headers.update({'craftName': 'PX4', 'fwType': 'PX4', 'tpa_percent': 0.})
        return (headers,)

    def _read_data(self, path: str) -> Tuple[dict]:
        try:
            from pyulog import ULog
        except ImportError as e:
            raise ImportError("PX4/.ulg support requires the 'pyulog' package "
                              "(pip install pyulog)") from e

        ulog = ULog(path, ['sensor_combined', 'vehicle_rates_setpoint', 'actuator_controls_0'])
        sensor_combined = ulog.get_dataset('sensor_combined')
        vehicle_rates_setpoint = ulog.get_dataset('vehicle_rates_setpoint')
        actuator_controls_0 = ulog.get_dataset('actuator_controls_0')

        time_us = sensor_combined.data['timestamp']
        time = time_us / 1e6

        def resample(topic_time, values):
            return interp1d(topic_time, values, **_RESAMPLE_KWARGS)(time_us)

        throttle = resample(actuator_controls_0.data['timestamp'],
                            actuator_controls_0.data['control[3]'] * 100.)

        traces = []
        for i, axis in enumerate(['roll', 'pitch', 'yaw']):
            gyro = np.rad2deg(sensor_combined.data['gyro_rad[%d]' % i])
            setpoint = np.rad2deg(resample(vehicle_rates_setpoint.data['timestamp'],
                                           vehicle_rates_setpoint.data[axis]))
            traces.append({'name': axis, 'time': time, 'gyro': gyro, 'input': setpoint,
                           'throttle': throttle})

        return ({'traces': traces},)
