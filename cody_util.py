def to_unsigned(n, bits: int = 16, convert: bool = False) -> int:
    if convert:
        n = int(n)
    else:
        assert isinstance(n, int)
    return n & ((1 << bits) - 1)


def twos_complement(n, bits: int = 16, convert: bool = False) -> int:
    u = to_unsigned(n, bits=bits, convert=convert)
    if u & (1 << (bits - 1)):  # test sign bit
        return u - (1 << bits)
    else:
        return u


def check_string(s, convert: bool = False) -> str:
    if convert:
        s = str(s)
    else:
        assert isinstance(s, str)
    assert len(s) <= 255 and all(map(lambda c: 0 <= ord(c) < 256, s))
    return s
