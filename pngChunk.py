import logging
import io
import zlib

import numpy as np
import matplotlib.pyplot as plt

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



class PngChunkcHRM(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        # value times 100000
        white_point_x = int.from_bytes(self._byte_data[:4], "big")
        white_point_y = int.from_bytes(self._byte_data[4:8], "big")
        red_x = int.from_bytes(self._byte_data[8:12], "big")
        red_y = int.from_bytes(self._byte_data[12:16], "big")
        green_x = int.from_bytes(self._byte_data[16:20], "big")
        green_y = int.from_bytes(self._byte_data[20:24], "big")
        blue_x = int.from_bytes(self._byte_data[24:28], "big")
        blue_y = int.from_bytes(self._byte_data[28:32], "big")

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
        pass

    def decode(self, color_type, data_dict: dict):
        logging.info("decode1")
        if color_type == 0 or color_type == 4:
            logging.info("decode2")
            greyscale = int.from_bytes(self._byte_data[0:2], "big")
            logging.info("greyscale %s", greyscale)
            self.data_dict["greyscale"] = greyscale

        if color_type == 2 or color_type == 6:
            red = int.from_bytes(self._byte_data[0:2], "big")
            green = int.from_bytes(self._byte_data[2:4], "big")
            blue = int.from_bytes(self._byte_data[4:6], "big")
            logging.info("red %s", red)
            logging.info("green %s", green)
            logging.info("blue %s", blue)

        if color_type == 3:
            palette_index = int.from_bytes(self._byte_data[0:1], "big")
            logging.info("palette_index %s", palette_index)



# data to filter and compress
class PngChunkIDAT(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        logging.info("Test")


    def decode(self, color_type):
        decoded = zlib.decompress(self._byte_data)
        cursor_1 = 0
        while cursor_1 < len(decoded):
            colorIndex = decoded[cursor_1]
            cursor_1 += 1
            print("colorIndex: " + str(colorIndex))





# image offset
class PngChunkoFFs(PngChunk):
    UNIT_SPECIFIER = {
        0 : "pixel",
        1 : "micrometer"
    }

    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        position_x = int.from_bytes(self._byte_data[0:4], "big", signed=True)
        position_y = int.from_bytes(self._byte_data[4:8], "big", signed=True)
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
        pixels_pu_x = int.from_bytes(self._byte_data[0:4], "big", signed=True)
        pixels_pu_y = int.from_bytes(self._byte_data[4:8], "big", signed=True)
        unit = self._byte_data[8]

        data_dict["Position x"] = pixels_pu_x
        data_dict["Position y"] = pixels_pu_y
        data_dict["Unit"] = unit

        logging.debug("Position x = %s", pixels_pu_x)
        logging.debug("Position y = %s", pixels_pu_y)
        logging.debug("Unit is the %s",
                      self.UNIT_SPECIFIER[unit])



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



# kolejne wystąpienia odpowiadają kolorom z chunka PLTE
class PngChunkhIST(PngChunk):
   def __init__(self, file: io.BufferedReader) -> None:
       super().__init__(file)

   def _parse_data(self, data_dict: dict):

       # dla pętli potrzebny jest dostęp do długości chunka
       hist=[]

       for i in range(20):
           hist.append(int.from_bytes(self._byte_data[2*i:2*i+2], "big"))

       # proba histogramu
       # data_dict["Histogram"] = hist
       # logging.debug("Histogram = %s", hist)
       # counts, bins = np.histogram(hist, range(257))
       # plt.bar(bins[:-1] - 0.5, counts, width=1, edgecolor='none')
       # plt.xlim([-0.5, 255.5])
       # plt.show()


class PngChunkPLTE(PngChunk):
    def __init__(self, file: io.BufferedReader) -> None:
        super().__init__(file)

    def _parse_data(self, data_dict: dict):
        red = []
        green = []
        blue = []
        # dla pętli potrzebny jest dostęp do długości chunka
        for i in range(self._length - 2):
            red.append(self._byte_data[i])
            green.append(self._byte_data[i+1])
            blue.append(self._byte_data[i+2])
        data_dict["PLTE R"] = red
        data_dict["PLTE G"] = green
        data_dict["PLTE B"] = blue
        logging.debug("PLTE R = %s", red)
        logging.debug("PLTE G = %s", green)
        logging.debug("PLTE B = %s", blue)



#class PngChunksBIT(PngChunk):


#class PngChunksPLT(PngChunk):


#class PngChunktRNS(PngChunk):


# compressed equivalent of tEXt
# class PngChunkzTXt(PngChunk):
