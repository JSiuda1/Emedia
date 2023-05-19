import logging
import numpy as np

from pngChunk import PngChunk

class PngFile(object):
    HEADER = b'\x89PNG\r\n\x1a\n'
    def __init__(self, file_path) -> None:
        self.file = open(file_path, "br")
        self._chunks = []

        self.__check_header()
        self.__load_chunks()

    def __check_header(self):
        header = self.file.read(8)
        logging.debug("Header: %s",header)

        if header != self.HEADER:
            raise RuntimeError(f"Invalid header {header}")

        return header

    def __load_chunks(self):
        self._chunks.append(PngChunk(self.file))
        while self._chunks[-1].type != "IEND":
            self._chunks.append(PngChunk(self.file))

    def get_fft(self) -> list[tuple]:
        x = range(0, 30)
        y = np.random.randint(0, 100, 30)
        return [(x,y), (x, y), (x, y)]


    @property
    def chunks(self):
        return self._chunks