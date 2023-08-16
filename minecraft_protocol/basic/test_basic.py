import pytest
import fields
def test_var():
    varint = fields.VarInt()
    varint.value = 128
    assert varint.serialize() == b"\x80\x01"
    varint.deserialize(b"\x80\x01")
    assert varint.value == 128
    varint.value = -1
    assert varint.serialize() == b"\xff\xff\xff\xff\x0f"
    assert varint.deserialize(b"\xff\xff\xff\xff\x0f") == 5
    assert varint.value == -1
    
    try:
        varint.serialize("\xff\xff\xff\xff\xff\x0f")
        raise AssertionError("VarInt is too big")
    except:
        print("VarInt oversize passed")
    varlong = fields.VarLong()
    try:
        varlong.serialize("\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0f")
        raise AssertionError("VarLong is too big")
    except:
        print("VarLong oversize passed")

if __name__ == "__main__": # debug
    test_var()