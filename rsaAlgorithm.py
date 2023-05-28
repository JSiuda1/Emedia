import sympy
import logging

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

        exp_size = key_size_bits // 2
        p = sympy.randprime(2**exp_size, 2**(exp_size+1) + 1)
        q = sympy.randprime(2**exp_size, 2**(exp_size+1) + 1)
        n = p * q
        phi = (p - 1) * (q - 1)
        e =  sympy.randprime(2**(exp_size - 1), phi)
        while e < phi and sympy.gcd(e, phi) != 1:
            e = sympy.randprime(2**(exp_size - 1), phi)

        d = sympy.mod_inverse(e, phi)

        self._public_key = PublicKey(n, e)
        self._private_key = PrivateKey(n, d)

        self._block_size_bit = key_size_bits // 8

    @property
    def public_key(self) -> PublicKey:
        return self._public_key

    @property
    def private_key(self) -> PrivateKey:
        return self._private_key

    def encrypt_data(self, data: int) -> int:
        return pow(data, self._public_key.e, self._public_key.n)

    def decrypt_data(self, data:int) -> int:
        return pow(data, self._private_key.d, self._private_key.n)

    def encrypt_ECB(self, chunk_data : bytes) -> bytes:
        encrypted_data = b''
        extra_data = b''

        chunk_data_blocks = [chunk_data[i:i + self._block_size_bit] for i in range(0, len(chunk_data), self._block_size_bit)]

        for data_block in chunk_data_blocks:
            encrypted_int: int = encrypted_data(int.from_bytes(data_block, "big"))
            encrypted_block = encrypted_int.to_bytes(self._block_size_bit, "big")

            if len(encrypted_block) < self._block_size_bit:
                encrypted_data += encrypted_block
            else:
                encrypted_data += encrypted_block[:self._block_size_bit]
                extra_data += encrypted_block[self._block_size_bit:]
                logging.info(extra_data)

        return encrypted_data, extra_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test = AlgorithmRSA(1024)
    a = test.encrypt_data(12)
    print(a)
    b = test.decrypt_data(a)
    print(b)