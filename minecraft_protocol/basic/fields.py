from abc import abstractmethod
from typing import Self
# MCObject
class MCObj:
    @property
    @abstractmethod
    def value(self):
        pass
    @value.setter
    @abstractmethod
    def value(self, value):
        pass
    @abstractmethod
    def serialize(self) -> bytes:
        pass
    @abstractmethod
    def deserialize(self, data:bytes) -> int:
        pass
    
    def with_value(self, value) -> Self:
        self.value = value
        return self

#MCNumber
class MCNumber(MCObj):
    _value: int
    length: int
    signed: bool
    def __init__(self, value, length, signed):
        self._value = value
        self.length = length
        self.signed = signed

    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, value: int):
        self._value = value
 
    def serialize(self) -> bytes:
        return self._value.to_bytes(self.length, byteorder="big", signed=self.signed)
    def deserialize(self, data: bytes) -> int:
        if(len(data) > self.length):
            raise ValueError(f"data is too long:{len(data)}bytes")
        self._value = int.from_bytes(data, "big", self.signed)
        return self.length

def Byte(value=0):
    return MCNumber(value, 1, True)
def Short(value=0):
    return MCNumber(value, 2, True)
def Integer(value=0):
    return MCNumber(value, 4, True)
def Long(value=0):
    return MCNumber(value, 8, True)
def UnsignedByte(value=0):
    return MCNumber(value, 1, False)
def UnsignedShort(value=0):
    return MCNumber(value, 2, False)
def UnsignedInteger(value=0):
    return MCNumber(value, 4, False)
def UnsignedLong(value=0):
    return MCNumber(value, 8, False)

# VarNumber
class VarNumber(MCObj):
    _value = 0
    length:int
    def __init__(self, length) -> None:
        self.length = length
    @property
    def value(self) -> int:
        return self._value
    @value.setter
    def value(self, value):
        self._value = value
    def serialize(self) -> bytes:
        value = self._value
        if value < 0:
            value = 2**self.length + self._value # 去符号（Python的补码真的是不知道说什么好了，正在试图让它正常点）
        buf = bytearray()
        while True:
            tmp = value & 0b01111111
            value = value >> 7
            if value != 0:
                tmp |= 0b10000000
            buf.append(tmp)
            if value == 0:
                break
        return bytes(buf)
    def deserialize(self, data: bytes) -> int:
        bytes_readed = 0
        result = 0
        while True:
            tmp = data[0]
            data = data[1:]
            int_value = tmp & 0b01111111 #忽略第一位提取整数
            result |= (int_value << (7 * bytes_readed))
            bytes_readed += 1
            if bytes_readed > self.length * 0.15625:
                raise ValueError("VarInt is too big (> 5 bytes)")
            if tmp & 0b10000000 == 0: # 第一位是0表示没有下一个字节
                # 再把其他语言的负整数转回Python的阴间格式
                if result >> 31 == 1:
                    self._value = result - 2 ** self.length
                else:
                    self._value = result
                return bytes_readed
        
def VarInt() -> VarNumber:
    return VarNumber(32)
def VarLong() -> VarNumber:
    return VarNumber(64)

# String
class MCString(MCObj):
    length = VarInt()
    _value = ""
    @property
    def value(self) -> str:
        return self._value
    @value.setter
    def value(self, value):
        self._value = value
        self.length.value = len(self._value)
    def __len__(self) -> int:
        return self.length.value
    def __str__(self) -> str:
        return self.value
    def serialize(self) -> bytes:
        return self.length.serialize() + self._value.encode("utf-8")
    def deserialize(self, data: bytes) -> int:
        length_len = self.length.deserialize(data)
        self._value = data[length_len:].decode("utf-8")
        return length_len + self.length.value
    