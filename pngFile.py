import logging
import numpy as np
import cv2
import matplotlib.pyplot as plt;
from pngChunk import PngChunk

class PngFile(object):
    HEADER = b'\x89PNG\r\n\x1a\n'
    def __init__(self, file_path) -> None:
        self.path_to_file = file_path
        self.file = open(file_path, "br")
        self._chunks = []

        self.__check_header()
        self.__load_chunks()
        # self._decode_picture()
        self.get_fft()

    def _check_color(self):
        res = next((chunk for chunk in self.chunks if chunk.type == "IHDR"), None)
        if res is not None:
            return res.color_type
        else:
            raise RuntimeError("IHDR chunk not found")

    def _decode_picture(self, data_dict: dict):
        color = self._check_color()
        for chunk in self.chunks:
            if chunk.type == "IDAT":
                chunk.decode(color, dict)
            if chunk.type == "bKGD":
                chunk.decode(color, dict)


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

    def get_fft(self):
        image = cv2.imread(self.path_to_file, cv2.IMREAD_GRAYSCALE)
        print(image.shape)
        # if len(image.shape) == 3:
        #     image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        #     fft = np.fft.fft2(image)
        #     fft_shifted = np.fft.fftshift(fft)

        #     fft_mag = np.log10(abs(fft_shifted.transpose()))
        # else:
        fft = np.fft.fft2(image)
        fft_shifted = np.fft.fftshift(fft)

        fft_mag = abs(fft_shifted.transpose())

        fft_phase = np.angle(fft_shifted.transpose())

        return (fft_mag, fft_mag)


    @property
    def chunks(self):
        return self._chunks


if __name__ == "__main__":
    test = PngFile("png/land.png")