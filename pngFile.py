import logging
import numpy as np
import zlib
import cv2
from pngChunk import PngChunk
import png

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

    def get_image_size(self) -> tuple[int]:
        ihdr = self.get_chunk("IHDR")
        return (ihdr.data["width"], ihdr.data["length"])

    def get_image_bytes_per_pixel(self) -> int:
        color_type_to_bytes = {
            0: 1,
            2: 3,
            3: 1,
            4: 2,
            6: 4,
        }

        color_type = self.get_image_color_type()
        if self.get_image_bit_depth() == 16:
            raise RuntimeError("Unsupported bit depth")

        return color_type_to_bytes[color_type]

    def get_image_color_type(self) -> int:
        return self.get_chunk("IHDR").data["color_type"]

    def get_image_filter_method(self) -> int:
        return self.get_chunk("IHDR").data["filter_method"]

    def get_image_bit_depth(self) -> int:
        return self.get_chunk("IHDR").data["bit_depth"]

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

    def save_image(self, path_to_save):
        self.build_png_from_chunks(path_to_save, self.cipher_data, self.padding)
        # file = open(path_to_save, "wb")
        # file.write(self.HEADER)
        # for chunk in self._chunks:
        #     file.write(chunk.create_chunk())
        # file.write(self.padding)


    def load_new_image(self, file_path):
        super().__init__(file_path)
        self.data_after_IEND = self.file.read()
        logging.info(f"After IEND len: {len(self.data_after_IEND)}")

    def get_decompersed_data(self) -> bytes:
        idat_data = self.get_all_data()
        idat_decompres = zlib.decompress(idat_data)
        w, l = self.get_image_size()
        bpp = self.get_image_bytes_per_pixel()

        if len(idat_decompres) != l * (1 + w * bpp):
            raise RuntimeError("Data corrupted")

        return self.defilter_data(idat_decompres)

    # def decode_data_ECB(self):
    #     self.cipher_data, self.padding = self.rsa.encrypt_ECB(self.get_all_data())

    # def encode_data_ECB(self):
    #     self.cipher_data = self.rsa.decrypt_ECB(self.get_all_data(), self.data_after_IEND)

    def decode_decompresed_data_ECB(self):
        data = self.get_decompersed_data()
        self.cipher_data, self.padding = self.rsa.encrypt_ECB(data)

    def encode_decompresed_data_ECB(self):
        data = self.get_decompersed_data()
        self.cipher_data = self.rsa.decrypt_ECB(data, self.data_after_IEND)
        self.padding = b''
        # self.build_png_from_chunks("dupa2.png", self.decrypted_data)

    def decode_decompresed_data_CBC(self):
        data = self.get_decompersed_data()
        self.cipher_data, self.padding = self.rsa.encrypt_CBC(data)

    def encode_decompresed_data_CBC(self):
        data = self.get_decompersed_data()
        self.cipher_data = self.rsa.decrypt_CBC(data, self.data_after_IEND)
        self.padding = b''
        # self.build_png_from_chunks("dupa2.png", self.decrypted_data)

    def _get_png_writer(self) -> png.Writer:
        w, l = self.get_image_size()
        bit_depth = self.get_image_bit_depth()
        color_type = self.get_image_color_type()
        greyscale = True
        alpha = False

        if color_type == 2:
            greyscale = False
            alpha = False
        elif color_type == 6:
            greyscale = False
            alpha = True
        elif color_type == 0:
            greyscale = True
            alpha = False

        return png.Writer(w, l, greyscale = greyscale, alpha = alpha, bitdepth = bit_depth)

    def build_png_from_chunks(self, file_name: str, pixels, after_iend_data = b'') -> bool:
        w, l = self.get_image_size()
        logging.info(f"Width {w}, Length {l}")
        bit_depth = self.get_image_bit_depth()
        writer = self._get_png_writer()

        row_width = w * self.get_image_bytes_per_pixel()
        pixels_by_rows = [pixels[i:i+row_width]
                          for i in range(0, len(pixels), row_width)]

        for row in pixels_by_rows:
            if len(row) < row_width and type(row) == list:
                row.extend([0]*(row_width-len(row)))

        with open(file_name, 'wb') as f:
            writer.write(f, pixels_by_rows)
            f.write(after_iend_data)

    def defilter_data(self, data_to_defilter: bytes):
        bytes_per_pixel = self.get_image_bytes_per_pixel()
        width, height = self.get_image_size()
        stride = width * bytes_per_pixel

        reconstructed_idat_data = b''

        def paeth_predictor(a, b, c):
            """The Paeth Predictor computes a simple linear function of the three neighboring pixels (left, above, upper left),
            then chooses as predictor the neighboring pixel closest to the computed value.
            This technique is due to Alan W. Paeth [1]."""
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c
            return Pr

        def recon_a(r, c):
            return reconstructed_idat_data[r * stride + c - bytes_per_pixel] if c >= bytes_per_pixel else 0

        def recon_b(r, c):
            return reconstructed_idat_data[(r-1) * stride + c] if r > 0 else 0

        def recon_c(r, c):
            return reconstructed_idat_data[(r-1) * stride + c - bytes_per_pixel] if r > 0 and c >= bytes_per_pixel else 0

        i = 0
        # print(stride * height, len(data_to_defilter))
        for r in range(height):
            filter_type = data_to_defilter[i]
            i += 1
            for c in range(stride):
                filt_x = data_to_defilter[i]
                i += 1
                if filter_type == 0:  # None
                    recon_x = filt_x
                elif filter_type == 1:  # Sub
                    recon_x = filt_x + recon_a(r, c)
                elif filter_type == 2:  # Up
                    recon_x = filt_x + recon_b(r, c)
                elif filter_type == 3:  # Average
                    recon_x = filt_x + (recon_a(r, c) + recon_b(r, c)) // 2
                elif filter_type == 4:  # Paeth
                    recon_x = filt_x + \
                        paeth_predictor(
                            recon_a(r, c), recon_b(r, c), recon_c(r, c))
                else:
                    raise Exception('Invalid filter type')
                reconstructed_idat_data += bytes([recon_x & 0xFF])
                # print(i)
        return reconstructed_idat_data



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    file = "png/test.png"
    test = PngFileCipher(file)
    test.decode_decompresed_data_ECB()
    test.save_image("sz_ecb_dec.png")
    test.load_new_image("sz_ecb_dec.png")
    test.encode_decompresed_data_ECB()
    test.save_image("sz_ecb_enc.png")

    test.load_new_image(file)
    test.decode_decompresed_data_CBC()
    test.save_image("sz_cbc_dec.png")
    test.load_new_image("sz_cbc_dec.png")
    test.encode_decompresed_data_CBC()
    test.save_image("sz_cbc_enc.png")
