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
        # self.get_fft()

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

    def __is_gray(self):
        img = cv2.imread(self.path_to_file)
        if len(img.shape) < 3: return True
        if img.shape[2]  == 1: return True
        b,g,r = img[:,:,0], img[:,:,1], img[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False



    def get_fft(self):
        fft_log = True
        if self.__is_gray():
            fft_log = False

        # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.imread(self.path_to_file, 0)
        fft = np.fft.fft2(image)
        fft_shifted = np.fft.fftshift(fft)

        if fft_log:
            fft_mag = np.ma.log10(abs(fft_shifted.transpose()))
        else:
            fft_mag = abs(fft_shifted.transpose())


        fft_phase = np.angle(fft_shifted.transpose())

        return (fft_mag, fft_phase)

    def get_chunk(self, name: str):
        res = next((chunk for chunk in self._chunks if chunk.type == name), None)
        return res

    def get_all_data(self):
        idat_chunks_data = [chunk.byte_data for chunk in self._chunks if chunk.type == "IDAT"]
        return b''.join(idat_chunks_data)

    @property
    def chunks(self):
        return self._chunks

from rsaAlgorithm import AlgorithmRSA

class PngFileCipher(PngFile):
    def __init__(self, file_path) -> None:
        super().__init__(file_path)
        self.data_after_IEND = self.file.read()
        logging.info(f"After IEND: {self.data_after_IEND}")
        self.rsa = AlgorithmRSA(256)

    def replace_IDAT(self, data: bytes):
        data_array = bytearray(data)
        for chunk in self._chunks:
            if chunk.type == "IDAT":
                chunk.set_data(data_array[:chunk.chunk_length])
                del data_array[:chunk.chunk_length]


    def decode_data_ECB(self):
        self.encrypted_data, self.padding = self.rsa.encrypt_ECB(self.get_all_data())
        self.replace_IDAT(self.encrypted_data)

    def encode_data_ECB(self):
        decoded_data = self.rsa.decrypt_ECB(self.get_all_data(), self.data_after_IEND)
        self.replace_IDAT(decoded_data)


    def save_image(self, path_to_save):
        file = open(path_to_save, "wb")
        file.write(self.HEADER)
        for chunk in self._chunks:
            file.write(chunk.create_chunk())
        file.write(self.padding)

    def load_new_image(self, file_path):
        super().__init__(file_path)
        self.data_after_IEND = self.file.read()
        logging.info(f"After IEND: {self.data_after_IEND}")



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test = PngFileCipher("png/crab.png")
    test.get_all_data()
    test.decode_data_ECB()
    test.save_image("test.png")
    test.load_new_image("test.png")
    test.encode_data_ECB()
    test.save_image("test2.png")

