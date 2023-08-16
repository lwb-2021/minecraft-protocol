from typing import List
from minecraft_protocol.basic.fields import MCObj, VarInt
from socket import socket
import zlib
class Packet:
    length = VarInt()
    _id = VarInt()
    decompressed_length = VarInt()
    data:bytes = None
    
    def __init__(self, **kwargs) -> None:
        if "id" in kwargs.keys():
            self._id.value = kwargs["id"]
            if "data" in kwargs.keys():
                self.data = kwargs["data"]
                self.length.value = len(self._id.serialize()) + len(self.data)
            else:
                self.length.value = len(self._id.serialize())
    @property
    def compressed(self) -> bool:
        return self.decompressed_length.value == 0
    
    @property
    def id(self) -> int:
        return self._id.value

    @id.setter
    def id(self, id):
        self._id.value = id
    
    
    def __len__(self):
        return self.length.value
        
    def read(self, socket: socket) -> int:
        # 解码length并切片
        buffer = socket.recv(5)
        if buffer == b"":
            return 0
        length_len = self.length.deserialize(buffer)
        buffer = buffer[length_len:]
        
        # 接受剩余字节
        buffer += socket.recv(self.length.value - (5 - length_len))
        # 解码id并将剩下的存入data
        id_len = self._id.deserialize(buffer)
        self.data = buffer[id_len:]
        
        # 返回length长度和后续内容的长度
        return length_len + self.length.value

    def read_compressed(self) -> int:
        # 解码length（Data Length+压缩后数据）并切片
        buffer = socket.recv(5)
        if buffer == b"":
            return 0
        length_len = self.length.deserialize(buffer)
        buffer = buffer[length_len:]
        
        # 接受剩余字节
        buffer += socket.recv(self.length.value - (5 - length_len))
        
        # 解码压缩前字节并切片
        decompressed_length_len = self.decompressed_length.deserialize(buffer)
        buffer = buffer[decompressed_length_len:]
        
        # 压缩过则解压
        if self.decompressed_length.value != 0:
            buffer = zlib.decompress(buffer, bufsize=self.decompressed_length.value)
        
        # 解码id并将剩下的存入data
        id_len = self._id.deserialize(buffer)
        self.data = buffer[id_len:]
        
        # 返回length的长度和后续内容的已压缩长度
        return length_len + self.length.value
        
    def send(self, socket:socket):
        socket.send(self.serialize())
        
    def send_compressed(self, socket:socket):
        socket.send(self.serialize_in_compressed_session())
    
    def send_uncompressed(self, socket:socket):
        socket.send(self.serialize_in_compressed_session(False))
    
    def serialize_in_compressed_session(self, compressed=True) -> bytes:
        if compressed:
            if self.data is not None:
                tmp = self.length.serialize() + zlib.compress(self._id.serialize() + self.data)
            else:
                tmp = self.length.serialize() + zlib.compress(self._id.serialize())
        else:
            tmp = "\x00" + self._id.serialize() + self.data
        length = VarInt().with_value(len(tmp))
        return length.serialize + tmp
        
    
    def serialize(self) -> bytes:
        if self.data is not None:
            return self.length.serialize() + self._id.serialize() + self.data
        else:
            return self.length.serialize() + self._id.serialize()
            
    def deserialize(self, fields:List[MCObj]) -> List[MCObj]:
        data = self.data
        for field in fields:
            length = field.deserialize(data)
            data = data[length:]
        return fields
        
class PacketBuilder():
    length = VarInt()
    id: int
    fields:List[MCObj] = []
    def __init__(self, id:int):
        self.id = id

    def add_field(self, field:MCObj):
        self.fields.append(field)
    
    def build(self) -> Packet:
        buffer = b""
        for field in self.fields:
            buffer += field.serialize()
        return Packet(id=self.id, data=buffer)


        


# for test

# if __name__ == "__main__":
#     from fields import *
#     from socket import create_connection
#     conn = create_connection(("127.0.0.1", 25565))
#     handshake = PacketBuilder(0)
#     handshake.add_field(VarInt().with_value(-1))
#     handshake.add_field(MCString().with_value("127.0.0.1"))
#     handshake.add_field(MCNumber(25565, 2, False))
#     handshake.add_field(VarInt().with_value(1))
#     handshake.build().send(conn)
#     response = Packet()
#     while True:
#         request = Packet(id=0)
#         request.send(conn)
#         length = response.read(conn)
#         if length != 0:
#             break
#     packet_result = response.deserialize([MCString()])
#     print(packet_result[0].value)
        
        