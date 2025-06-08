from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import ParseDict

def dict_to_struct(data: dict) -> Struct:
    struct = Struct()
    ParseDict(data or {}, struct)
    return struct