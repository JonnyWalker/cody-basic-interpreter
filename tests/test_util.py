from cody_util import twos_complement


def test_twos_complement_pos():
    assert twos_complement(0) == 0
    assert twos_complement(1) == 1
    assert twos_complement(127) == 127
    assert twos_complement(128) == 128
    assert twos_complement(255) == 255
    assert twos_complement(256) == 256
    assert twos_complement(32767) == 32767
    assert twos_complement(32768) == -32768
    assert twos_complement(65535) == -1
    assert twos_complement(65536) == 0


def test_twos_complement_neg():
    assert twos_complement(-1) == -1
    assert twos_complement(-128) == -128
    assert twos_complement(-129) == -129
    assert twos_complement(-256) == -256
    assert twos_complement(-257) == -257
    assert twos_complement(-32768) == -32768
    assert twos_complement(-32769) == 32767
    assert twos_complement(-65536) == 0
    assert twos_complement(-65537) == -1
