import logging

import pngChunk as chunk

class PngFile(object):
    HEADER = b'\x89PNG\r\n\x1a\n'
    def __init__(self, file_path) -> None:
        self.file = open(file_path, "br")
        self.chunks = []

        self.__check_header()
        self.__load_chunks()


    def __check_header(self):
        header = self.file.read(8)
        logging.debug("Header: %s",header)

        if header != self.HEADER:
            raise RuntimeError(f"Invalid header {header}")

        return header

    def __load_chunks(self):
        self.chunks.append(chunk.PngChunk(self.file))
        while self.chunks[-1].type != "IEND":
            self.chunks.append(chunk.PngChunk(self.file))