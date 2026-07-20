import subprocess
from typing import Tuple

from .blackbox_decode_csv_loader import BlackboxDecodeCsvLoader
from .loader import Loader
from ..common import *

# minimum size of a log to parse in bytes
LOG_MIN_BYTES = 500000
# blackbox logs can have multiple extensions
LOG_EXTENSIONS = [".bbl", ".bfl"]


class BblLoader(Loader):
    """Loads Betaflight blackbox log files.
    """
    
    def __init__(self, path: str, tmp_subdir: str = "tmp"):
        self.tmp_subdir = tmp_subdir
        super().__init__(path, tmp_subdir)

    @staticmethod
    def is_applicable(path: str) -> bool:
        # simply check file extension
        return os.path.splitext(path)[1].lower() in LOG_EXTENSIONS

    def _read_headers(self, path: str) -> Tuple[dict]:
        from ..common import DECODER_TYPE
        result = []
        csvfiles = self._bbl_to_csv()
        for i, csvpath in enumerate(csvfiles):
            _, ext = os.path.splitext(csvpath)
            # blackbox_decode always appends ".01.csv"; bbl_parser omits the
            # infix for a single-session input (which is always what it gets
            # here, since sessions are already split out above) and may
            # produce nothing at all if its own smart filtering skips this
            # segment (exits 0 either way, so existence must be checked).
            csv_suffix = ".csv" if DECODER_TYPE == 'bbl_parser' else ".01.csv"
            guessed_csv = csvpath.replace(ext, csv_suffix)
            if not os.path.isfile(guessed_csv):
                log.info('Skipping filtered/empty session: %r' % csvpath)
                continue
            headers = headerdict(guessed_csv, i)
            with open(csvpath, 'rb') as f:
                lines = f.readlines()
            # check for known keys and translate to useful ones.
            for raw_line in lines:
                line = raw_line.decode('latin-1')
                for key in FIELDS_MAP.keys():
                    if key in line:
                        val = line.split(':')[-1]
                        headers.update({FIELDS_MAP[key]: val[:-1]})
            result.append(headers)
        return tuple(result)

    def _read_data(self, path: str) -> Tuple[dict]:
        # load decoded CSV using the dedicated loader
        result = []
        for headers in self.headers:
            result.append(BlackboxDecodeCsvLoader(headers["tempFile"], self.tmp_subdir).data[0])
        return tuple(result)

    def _bbl_to_csv(self) -> list:
        """Splits out one BBL per recorded session and converts each to CSV.

        :return: a list containing paths of the resulting CSV files
        """
        with open(self.path, 'rb') as binary_log_view:
            content = binary_log_view.read()

        # The first line of the overall BBL file re-appears at the beginning
        # of each recorded session.
        try:
            first_newline_index = content.index(str('\n').encode('utf8'))
        except ValueError as e:
            raise ValueError('No newline in %dB of log data from %r.'
                             % (len(content), self.path), e)
        firstline = content[:first_newline_index + 1]

        split = content.split(firstline)
        bbl_sessions = []
        for i in range(len(split)):
            path_root, path_ext = os.path.splitext(os.path.basename(self.path))
            temp_path = os.path.join(self.tmp_path, '%s_temp%d%s' % (path_root, i, path_ext))
            with open(temp_path, 'wb') as newfile:
                newfile.write(firstline + split[i])
            bbl_sessions.append(temp_path)

        from ..common import BLACKBOX_DECODE_PATH, DECODER_TYPE, DECODER_FORCE_EXPORT
        loglist = []
        for bbl_session in bbl_sessions:
            size_bytes = os.path.getsize(os.path.join(self.tmp_path, bbl_session))
            if size_bytes > LOG_MIN_BYTES:
                try:
                    if DECODER_TYPE == 'bbl_parser':
                        cmd = [BLACKBOX_DECODE_PATH, '--output-dir', self.tmp_path]
                        if DECODER_FORCE_EXPORT:
                            cmd.append('--force-export')
                        cmd.append(bbl_session)
                    else:
                        cmd = [BLACKBOX_DECODE_PATH, bbl_session]
                    subprocess.check_call(cmd)
                    output_path = os.path.join(self.tmp_path, bbl_session)
                    loglist.append(output_path)
                except subprocess.CalledProcessError:
                    log.error('Error decoding %r' % bbl_session, exc_info=True)
            else:
                # There is often a small bogus session at the start of the file.
                log.warning('Ignoring BBL session %r, %dB < %dB.'
                            % (bbl_session, size_bytes, LOG_MIN_BYTES))
                os.remove(bbl_session)

        return loglist
