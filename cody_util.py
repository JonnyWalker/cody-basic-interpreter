from typing import Literal


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


def check_string(
    s,
    convert: bool = False,
    allowed_chars: Literal[
        "any", "ascii", "petscii", "printable", "ascii_printable"
    ] = "any",
) -> str:
    if convert:
        s = str(s)
    else:
        assert isinstance(s, str)
    if len(s) > 255:
        raise ValueError("string too long")
    for c in s:
        n = ord(c)
        if allowed_chars == "any":
            if 0 <= n < 256:
                continue
        elif allowed_chars == "ascii":
            if 0 <= n < 128:
                continue
        elif allowed_chars == "petscii":
            if 128 <= n < 256:
                continue
        elif allowed_chars == "printable":
            if is_printable(n):
                continue
        elif allowed_chars == "ascii_printable":
            if 0 <= n < 128 and is_printable(n):
                continue
        else:
            raise ValueError(f"unknown allowed_chars {allowed_chars}")
        raise ValueError(f"invalid character with codepoint {n}")
    return s


def is_printable(c: str | int):
    if isinstance(c, str):
        c = ord(c)
    return 32 <= c < 222 and c != 127
