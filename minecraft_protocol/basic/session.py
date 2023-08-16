from minecraft_protocol.basic.packet import PacketBuilder
from minecraft_protocol.basic.fields import *
from socket import socket, create_connection

class Session:
    host: str
    port: int
    conn: socket
    online = False
    
    STATUS_STATUS = 1
    STATUS_LOGIN = 2
    
    def __init__(self, host:str, port:int) -> None:
        self.host = host
        self.port = port
    
    def connect(self):
        self.conn = create_connection(self.host, self.port)
    
    def handshake(self, next_status=1):
        handshake = PacketBuilder(0)
        handshake.add_field(VarInt().with_value(-1))
        handshake.add_field(MCString().with_value(self.host))
        handshake.add_field(UnsignedShort(self.port, False))
        handshake.add_field(VarInt().with_value(next_status))
        handshake.build().send(self.conn)
    