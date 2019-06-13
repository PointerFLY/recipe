import gzip
import random
import bz2
import lzma

binary_map = {
    1: '001',
    2: '010',
    3: '011',
    4: '100',
    5: '101',
    6: '110'
}
# 000, 111


def generate() -> bytes:
    text = ''
    for i in range(1000000):
        num = random.randint(1, 6)
        text += chr(num)
    return text.encode('ascii')


if __name__ == '__main__':
    original = generate()

    compressed = bz2.compress(original)
    decompressed = bz2.decompress(compressed)
    assert decompressed == original

    print(len(compressed))

    ratio = len(compressed) / len(original)
    print(ratio)
