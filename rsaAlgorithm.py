import sympy
import logging
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA


# from cryptography.hazmat.primitives.ciphers.modes import CBC
# import pyaes

class PublicKey:
    def __init__(self, n: int, e: int) -> None:
        self._n = n
        self._e = e

    def __str__(self) -> str:
        return f"({self._n}, {self._e}"

    @property
    def n(self) -> int:
        return self._n

    @property
    def e(self) -> int:
        return self._e

class PrivateKey:
    def __init__(self, n: int, d: int) -> None:
        self._n = n
        self._d = d

    def __str__(self) -> str:
        return f"({self._n}, {self._d})"

    @property
    def n(self) -> int:
        return self._n

    @property
    def d(self) -> int:
        return self._d

class AlgorithmRSA:
    def __init__(self, key_size_bits = 2048) -> None:
        self._key_size_bits = key_size_bits
        exp_size = key_size_bits // 2
        p = sympy.randprime(2**(exp_size), 2**(exp_size + 1)- 1)
        q = sympy.randprime(2**(exp_size), 2**(exp_size + 1) - 1)
        n = p * q
        phi = (p - 1) * (q - 1)
        e =  sympy.randprime(2**(exp_size), phi)
        while e < phi and sympy.gcd(e, phi) != 1:
            e = sympy.randprime(2**(exp_size), phi)

        d = sympy.mod_inverse(e, phi)

        self._public_key = PublicKey(n, e)
        self._private_key = PrivateKey(n, d)

        self._block_size_bytes = key_size_bits // 8

    @property
    def public_key(self) -> PublicKey:
        return self._public_key

    @property
    def private_key(self) -> PrivateKey:
        return self._private_key

    def encrypt_data(self, data: bytes) -> bytes:
        res: int = pow(int.from_bytes(data, "big"), self._public_key.e, self._public_key.n)
        return res.to_bytes(self._block_size_bytes + 1, "big")

    def encrypt_data_int(self, data: int) -> bytes:
        res: int = pow(data, self._public_key.e, self._public_key.n)
        return res.to_bytes(self._block_size_bytes + 1, "big")

    def decrypt_data(self, data: bytes) -> bytes:
        res: int =  pow(int.from_bytes(data, "big"), self._private_key.d, self._private_key.n)
        return res.to_bytes(self._block_size_bytes + 1, "big")

    def generate_initialize_vector(self):
        return sympy.randprime(2**(self._key_size_bits // 2 - 1), 2**(self._key_size_bits // 2)- 1)

    def encrypt_CBC(self, chunk_data: bytes) -> tuple[bytes]:
        encrypted_data = b''
        padding_data = b''
        previous_data = self.generate_initialize_vector()
        padding_data += previous_data.to_bytes(self._block_size_bytes + 1, "big")
        # logging.info("Init vector: {}".format(padding_data))

        chunk_data_blocks = [chunk_data[i:i + self._block_size_bytes] for i in range(0, len(chunk_data), self._block_size_bytes)]

        for data_block in chunk_data_blocks:
            data_to_encrypt = int.from_bytes(data_block, "big")
            data_to_encrypt_int = data_to_encrypt ^ previous_data
            # logging.info("Data xor {}".format(data_to_encrypt_int.to_bytes(self._block_size_bytes + 1, "big")))
            data = self.encrypt_data_int(data_to_encrypt_int)

            previous_data = int.from_bytes(data[1:], "big")
            # logging.info("Prev data encrypr {}".format(previous_data.to_bytes(self._block_size_bytes + 1, "big")))

            if len(data_block) < (self._block_size_bytes):
                padding_size = self._block_size_bytes - len(data_block) + 1
                padding_data += data[:padding_size]
                encrypted_data += data[padding_size:]
                # logging.info(f"ENC data: {data}")
            else:
                padding_data += data[0].to_bytes(1, "big")
                encrypted_data += data[1:]
                # logging.info(f"ENC data: {data}")

        return encrypted_data, padding_data

    def decrypt_CBC(self, chunk_data: bytes, padding_data: bytes) -> bytes:
        chunk_data_blocks = [chunk_data[i:i + self._block_size_bytes] for i in range(0, len(chunk_data), self._block_size_bytes)]
        padding_data_array = bytearray(padding_data)

        previous_data = int.from_bytes(padding_data[:self._block_size_bytes + 1], "big")
        del padding_data_array[:self._block_size_bytes + 1]
        # logging.info(f"Init vector: {padding_data[:self._block_size_bytes + 1]}")

        decrypred_data = b''

        for data_block in chunk_data_blocks:
            if len(data_block) < self._block_size_bytes:
                padding_size = self._block_size_bytes - len(data_block) + 1 # +1 \x00 padding
                data_to_decrypt = bytes(padding_data_array[:padding_size] + data_block)
                del padding_data_array[:padding_size]

                # logging.info(f"DEC data: {data_to_decrypt}")
                data = self.decrypt_data(data_to_decrypt)
                # logging.info("Data xor {}".format(data))
                data_xor = int.from_bytes(data, "big") ^ previous_data
                data = data_xor.to_bytes(len(data), "big")
                decrypred_data += data[padding_size:]
                # logging.info(f"Data {data[padding_size:]}")
                previous_data = int.from_bytes(data_to_decrypt[1:], "big")
            else:
                data_to_decrypt = padding_data_array[0].to_bytes(1, "big") + data_block
                del padding_data_array[0]

                # logging.info(f"DEC data: {data_to_decrypt}")
                data = self.decrypt_data(data_to_decrypt)
                # logging.info("Data xor {}".format(data))
                data_xor = int.from_bytes(data, "big") ^ previous_data
                data = data_xor.to_bytes(len(data), "big")
                decrypred_data += data[1:]
                # logging.info(f"Data {data}")
                previous_data = int.from_bytes(data_to_decrypt[1:], "big")

            # logging.info("prev data decrypt {}".format(previous_data.to_bytes(self._block_size_bytes + 1, "big")))
        return decrypred_data


    def encrypt_ECB(self, chunk_data : bytes) -> tuple[bytes]:
        encrypted_data = b''
        padding_data = b''

        chunk_data_blocks = [chunk_data[i:i + self._block_size_bytes] for i in range(0, len(chunk_data), self._block_size_bytes)]
        for data_block in chunk_data_blocks:

            data = self.encrypt_data(data_block)

            if len(data_block) < (self._block_size_bytes):
                padding_size = self._block_size_bytes - len(data_block) + 1
                padding_data += data[:padding_size]
                encrypted_data += data[padding_size:]
            else:
                padding_data += data[0].to_bytes(1, "big")
                encrypted_data += data[1:]

        return encrypted_data, padding_data


    def encrypt_ECB_v2(self, chunk_data : bytes) -> tuple[bytes]:
        encrypted_data = b''
        padding_data = b''

        chunk_data_blocks = [chunk_data[i:i + self._block_size_bytes] for i in range(0, len(chunk_data), self._block_size_bytes)]

        key = RSA.construct((self._public_key.n, self._public_key.e))
        # key = self._public_key.n.to_bytes()
        cipher = AES.new(key.exportKey(format="DER"), AES.MODE_ECB)

        for data_block in chunk_data_blocks:

            data = cipher.encrypt(data_block)


            if len(data_block) < (self._block_size_bytes):
                padding_size = self._block_size_bytes - len(data_block) + 1
                padding_data += data[:padding_size]
                encrypted_data += data[padding_size:]
            else:
                padding_data += data[0].to_bytes(1, "big")
                encrypted_data += data[1:]

        return encrypted_data, padding_data


    def decrypt_ECB(self, chunk_data: bytes, padding_data: bytes) -> bytes:
        chunk_data_blocks = [chunk_data[i:i + self._block_size_bytes] for i in range(0, len(chunk_data), self._block_size_bytes)]
        padding_data_array = bytearray(padding_data)

        decrypred_data = b''
        # IDK
        for data_block in chunk_data_blocks:
            if len(data_block) < self._block_size_bytes:
                padding_size = self._block_size_bytes - len(data_block) + 1 # +1 \x00 padding
                data_to_decrypt = bytes(padding_data_array[:padding_size] + data_block)
                logging.info(f"Data to enc {data_to_decrypt}")
                del padding_data_array[:padding_size]
                data = self.decrypt_data(data_to_decrypt)
                decrypred_data += data[padding_size:]
            else:
                data_to_decrypt = padding_data_array[0].to_bytes(1, "big") + data_block
                del padding_data_array[0]
                data = self.decrypt_data(data_to_decrypt)
                decrypred_data += data[1:]

        return decrypred_data



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test = AlgorithmRSA(256)
    chunk_data = b'x\x9cc\xe8\xe8\x08\r=sf\xd5\xaa\xf2rc\xe3w\xeff\xced C\x00\x95+(H\x8e\x00*\xd7\xc5\x85\x1c\x01T\xee\xdd\xbb\xe4\x08\xa0q\x19\xc8\x11@\xe5*)\x91#\x80\xcaMK#G\x00\x95\xbb{7\x19\x02\x00\xe0\xc4\xea\xd1'
    # chunk_data = b'x\x9cc\xe8\xe8\x08\r=sf\xd5\xaa\xf2rc\xe3w\xeff\xced C\x00\x95+(H\x8e\x00*\xd7\xc5\x85\x1c\x01T\xee\xdd\xbb\xe4'
    for i in range(1000):
        result, padding = test.encrypt_CBC(chunk_data)
        out = test.decrypt_CBC(result, padding)
        # result, padding = test.encrypt_ECB(chunk_data)
        # out = test.decrypt_ECB(result, padding)
        # logging.info(f"Out {dec}")
        if chunk_data == out:
            logging.info(":D")
        else:
            logging.info(":C")
            raise Exception("DUPA")
