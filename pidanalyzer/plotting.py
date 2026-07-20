from typing import List, Tuple

import numpy as np

from .common import log
from .figures import noise_figure, response_figure
from .trace import Trace


def show_plots(name: str, header: dict, data: dict, noise_bounds: list):
    path = header["tempFile"]
    log.info("CSV file: " + path)
    log.info('Processing:')
    if 'traces' in data:
        # loader already built Trace-ready per-axis dicts (e.g. PX4/ULog, which has
        # no BF-style raw fields for _create_traces to parse)
        traces_header = dict(header)
        traces = []
        for axisdata in data['traces']:
            log.info(axisdata['name'] + '...   ')
            traces.append(Trace(axisdata))
    else:
        traces_header, traces = _create_traces(header, data)
    response_figure.create(path, name, traces_header, traces)
    if all(tr.has_noise_data for tr in traces):
        noise_figure.create(path, name, traces_header, traces, noise_bounds)
    else:
        log.info('Skipping noise plot: no D-term/debug data available.')


def _create_traces(header: dict, data: dict) -> Tuple[dict, List[Trace]]:
    time = data['time_us']
    throttle = ((data['throttle'] - 1000.) / (float(header['maxThrottle']) - 1000.)) * 100.
    tracesdata = [{'name': 'roll'}, {'name': 'pitch'}, {'name': 'yaw'}]
    traces_header = dict(header)
    # debug[3] holding data means the flightcontroller's debug_mode isn't exposing
    # prefiltered gyro data, so noise_figure can't produce a meaningful debug plot.
    traces_header.update({'correctdebugmode': not np.any(data.get('debug3', 0))})
    traces = []

    for i, axisdata in enumerate(tracesdata):
        axisdata.update({'time': time})
        si = str(i)
        axisdata.update({'p_err': data['PID loop in' + si]})
        axisdata.update({'rcinput': data['rcCommand' + si]})
        axisdata.update({'gyro': data['gyroData' + si]})
        axisdata.update({'PIDsum': data['PID sum' + si]})
        axisdata.update({'d_err': data['d_err' + si]})
        axisdata.update({'debug': data['debug' + si]})
        if 'KISS' in header['fwType']:
            axisdata.update({'P': 1.})
            traces_header.update({'tpa_percent': 0.})
        elif 'Raceflight' in header['fwType']:
            axisdata.update({'P': 1.})
            traces_header.update({'tpa_percent': 0.})
        else:
            axisdata.update({'P': float((header[axisdata['name'] + 'PID']).split(',')[0])})
            traces_header.update({'tpa_percent': (float(header['tpa_breakpoint']) - 1000.) / 10.})
        axisdata.update({'throttle': throttle})
        log.info(axisdata['name'] + '...   ')
        traces.append(Trace(axisdata))

    return traces_header, traces
