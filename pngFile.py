import logging

import pngChunk as chunk

class PngFile(object):
    HEADER = b'\x89PNG\r\n\x1a\n'
    def __init__(self, file_path) -> None:
        self.file = open(file_path, "br")
        self.chunks = []

        self.__check_header()
        self.__load_chunks()
#        self.color_type()
        self.__read_type()

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

    def color_type(self) -> int:
        color = self.color_type
        logging.debug("color type %d", color)
        return color


#    def __read_color_type(self):

#        chunk_type = self.file.read().decode()
#        logging.debug("%s", chunk_type)

