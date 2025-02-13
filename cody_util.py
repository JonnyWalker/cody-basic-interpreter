def to_unsigned(n, bits=16):
    return n & ((1 << bits) - 1)


def twos_complement(n, bits=16):
    u = to_unsigned(n, bits)
    if u & (1 << (bits - 1)):  # test sign bit
        return u - (1 << bits)
    else:
        return u
