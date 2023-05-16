import logging
import io
from terminalColors import bcolors

CHUNK_LENGTH_SIZE = 4
CHUNK_TYPE_SIZE = 4
CHUNK_CRC_SIZE = 4

class PngChunk(object):
    def __init__(self, file: io.BufferedReader) -> None:
        logging.debug(f"{bcolors.HEADER}{bcolors.BOLD}New chunk:{bcolors.ENDC}")

        self._file = file
        self._length = self.__read_length()
        self._type = self.__read_type()
        self._byte_data = self.__read_data()
        self._crc = self.__calculate_crc()

        self._data = {}
        if self.__change_object_to_specific_chunk() is True:
            self._parse_data(self._data)

    def __change_object_to_specific_chunk(self) -> bool:
        """Change class to specific chunt type class (in case of use parent class)"""
        if self.__class__ != PngChunk:
            return True
        try:
            self.__class__ = globals()[f"PngChunk{self._type}"]
        except Exception:
            return False
        return True

    def __read_length(self) -> int:
        """Read chunk length

        Returns:
            int: Chunk length
        """
        length = int.from_bytes(self._file.read(CHUNK_LENGTH_SIZE), 'big')
        logging.debug("Length %d", length)
        return length

    def __read_type(self) -> str:
        """Read chunk type

        Returns:
            str: Chunk type
        """
        chunk_type = self._file.read(CHUNK_TYPE_SIZE).decode()
        logging.debug(f"{bcolors.OKCYAN}{bcolors.BOLD}%s{bcolors.ENDC}", chunk_type)
        return chunk_type

    def __read_data(self) -> bytes:
        """Read chunk data

        Returns:
            bytes: Chunk data
        """
        data = self._file.read(self._length)
        logging.debug("Data %s...", data[:40])
        return data

    def __calculate_crc(self) -> int:
        """Calculate chunk crc
        """
        crc = int.from_bytes(self._file.read(CHUNK_CRC_SIZE), "big")
        logging.debug("CRC: %d", crc)
        return crc

    def _parse_data(self, data_dict: dict):
        """Parse chunk data"""
        raise NotImplementedError

    def is_critical(self) -> bytes:
        return self._type[0].isupper()

    def create_chunk(self):
        length_byte = self._length.to_bytes(4, 'big')
        type_byte = str.encode(self._type)
        crc_byte = self._crc.to_bytes(4, 'big')

        chunk_byte = length_byte + type_byte + self._byte_data + crc_byte
        return chunk_byte

    @property
    def type(self):
        return self._type

    @property
    def chunk_length(self):
        return self._length

    @property
    def byte_data(self):
        return self._byte_data

    @property
    def data(self):
        return self._data



class PngChunkIHDR(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        logging.debug("I am IHDR")
        super().__init__(file)

    @property
    def width(self) -> int:
        width = int.from_bytes(self._byte_data[:4], "big")
        logging.debug("Width %d", width)
        return width

    @property
    def length(self) -> int:
        length = int.from_bytes(self._byte_data[4:8], "big")
        logging.debug("length %d", length)
        return length

    @property
    def bit_depth(self) -> int:
        bit_depth = self._byte_data[9]
        logging.debug("bit_depth %d", bit_depth)
        return bit_depth

    @property
    def color_type(self) -> int:
        color = self._byte_data[10]
        logging.debug("color type %d", color)
        return color

    @property
    def compression_method(self) -> int:
        compression = self._byte_data[11]
        logging.debug("Compression method %d", compression)
        return compression

    @property
    def filter_method(self) -> int:
        filter_method = self._byte_data[11]
        logging.debug("Filter method %d", filter_method)
        return filter_method

    @property
    def interlace_method(self) -> int:
        interlace_method = self._byte_data[11]
        logging.debug("Interlace method %d", interlace_method)
        return interlace_method


    def _parse_data(self, data_dict:dict):
        data_dict["width"] = self.width
        data_dict["length"] = self.length
        data_dict["bit_depth"] = self.bit_depth
        data_dict["color_type"] = self.color_type
        data_dict["compression_method"] = self.compression_method
        data_dict["filter_method"] = self.filter_method
        data_dict["interlace_method"] = self.interlace_method


# class PngChunkIDAT(PngChunk):
#     pass


class PngChunkIEND(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        return


class PngChunkgAMA(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    @property
    def gamma(self) -> float:
        gamma = int.from_bytes(self._byte_data, "big")
        logging.debug("Gamma %f", gamma / 100000.0)
        return gamma / 100000.0

    def _parse_data(self, data_dict: dict):
        data_dict["gamma"] = self.gamma

class PngChunktEXt(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        pass

class PngChunksRGB(PngChunk):
    RENDERING_INTENT_DEF = {
        0 : "Perceptual",
        1 : "Relative colorimetric",
        2 : "Saturation",
        3 : "Absolute colorimetric"
    }

    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    @property
    def rendering_intent_value(self) -> int:
        rendering_intent = int.from_bytes(self._byte_data, "big")
        logging.debug("Rendering intent %d -> %s",
                        rendering_intent,
                        self.RENDERING_INTENT_DEF[rendering_intent])
        return rendering_intent

    @property
    def rendering_intent_string(self) -> str:
        return self.RENDERING_INTENT_DEF[self.rendering_intent_value]

    def _parse_data(self, data_dict: dict):
        data_dict["rendering_intent"] = self.rendering_intent_string


class PngChunktEXt(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        data = self._byte_data.decode().split('\0')
        data_dict["keyword"] = data[0]
        data_dict["text"] = data[1]
        logging.debug("Keyword %s", data[0])
        logging.debug("Text %s", data[1])