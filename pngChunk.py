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

    def __calculate_crc(self):
        """Calculate chunk crc
        """
        crc = int.from_bytes(self._file.read(CHUNK_CRC_SIZE), "big")
        logging.debug("CRC: %d", crc)

    def _parse_data(self, data_dict: dict):
        """Parse chunk data"""
        raise NotImplementedError

    @property
    def type(self):
        return self._type


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



class PngChunkcHRM(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        # value times 100000
        white_point_x = int.from_bytes(self._byte_data[:4], "big")
        white_point_y = int.from_bytes(self._byte_data[5:8], "big")
        red_x = int.from_bytes(self._byte_data[9:12], "big")
        red_y = int.from_bytes(self._byte_data[13:16], "big")
        green_x = int.from_bytes(self._byte_data[17:20], "big")
        green_y = int.from_bytes(self._byte_data[21:24], "big")
        blue_x = int.from_bytes(self._byte_data[25:28], "big")
        blue_y = int.from_bytes(self._byte_data[29:32], "big")

        data_dict["White point x"] = white_point_x/100000
        data_dict["White point y"] = white_point_y/100000
        data_dict["Red x"] = red_x/100000
        data_dict["Red y"] = red_y/100000
        data_dict["Green x"] = green_x/100000
        data_dict["Green y"] = green_y/100000
        data_dict["Blue x"] = blue_x/100000
        data_dict["Blue y"] = blue_y/100000

        logging.debug("White point x = %s", white_point_x/100000)
        logging.debug("White point y = %s", white_point_y / 100000)
        logging.debug("Red x = %s", red_x / 100000)
        logging.debug("Red y = %s", red_y / 100000)
        logging.debug("Green x = %s", green_x / 100000)
        logging.debug("Green y = %s", green_y / 100000)
        logging.debug("Blue x = %s", blue_x / 100000)
        logging.debug("Blue y = %s", blue_y / 100000)


class PngChunkbKGD(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        palette_index = int.from_bytes(self._byte_data[:1], "big")

        data_dict["palette index"] = palette_index

      #  if self.color_type
        logging.debug("White point x = %s", palette_index)


# data to filter and compress
#class PngChunkIDAT(PngChunk):
#    pass


# 2 byte data series of each frequency
# tutaj trzebaby jakąś pętlę zrobić
class PngChunkhIST(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        freq = int.from_bytes(self._byte_data[:3], "big")
        data_dict["Frequency 1"] = freq
        logging.debug("Frequency 1 = %s", freq)


# image offset
class PngChunkoFFs(PngChunk):
    UNIT_SPECIFIER = {
        0 : "pixel",
        1 : "micrometer"
    }

    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        position_x = int.from_bytes(self._byte_data[:4], "big")
        position_y = int.from_bytes(self._byte_data[5:8], "big")
        unit = self._byte_data[8]

        data_dict["Position x"] = position_x
        data_dict["Position y"] = position_y
        data_dict["Unit"] = unit

        logging.debug("Position x = %s", position_x)
        logging.debug("Position y = %s", position_y)
        logging.debug("Unit is the %s",
                      self.UNIT_SPECIFIER[unit])


class PngChunkpHYs(PngChunk):
    UNIT_SPECIFIER = {
        0 : "unknown",
        1 : "meter"
    }

    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

# pixels per unit
    def _parse_data(self, data_dict: dict):
        pixels_pu_x = int.from_bytes(self._byte_data[:4], "big")
        pixels_pu_y = int.from_bytes(self._byte_data[5:8], "big")
        unit = self._byte_data[8]

        data_dict["Position x"] = pixels_pu_x
        data_dict["Position y"] = pixels_pu_y
        data_dict["Unit"] = unit

        logging.debug("Position x = %s", pixels_pu_x)
        logging.debug("Position y = %s", pixels_pu_y)
        logging.debug("Unit is the %s",
                      self.UNIT_SPECIFIER[unit])


#class PngChunksBIT(PngChunk):


#class PngChunksPLT(PngChunk):


class PngChunksTER(PngChunk):
    LAYOUT_TYPE = {
        0 : "cross-fuse layout",
        1 : "diverging-fuse layout"
    }
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        layout_type = self._byte_data[0]

        data_dict["Layout type"] = layout_type

        logging.debug("Layout type is the %s",
                      self.LAYOUT_TYPE[layout_type])
#        logging.debug("cos %d", data_dict["length"])


class PngChunktIME(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        year = int.from_bytes(self._byte_data[:2], "big")
        month = self._byte_data[2]
        day = self._byte_data[3]
        hour = self._byte_data[4]
        minute = self._byte_data[5]
        second = self._byte_data[6]

        data_dict["year"] = year
        data_dict["month"] = month
        data_dict["day"] = day
        data_dict["hour"] = hour
        data_dict["minute"] = minute
        data_dict["second"] = second

        logging.debug("year %s", year)
        logging.debug("month %s", month)
        logging.debug("day %s", day)
        logging.debug("hour %s", hour)
        logging.debug("minute %s", minute)
        logging.debug("second %s", second)

#class PngChunktRNS(PngChunk):


# compressed equivalent of tEXt
# class PngChunkzTXt(PngChunk):

