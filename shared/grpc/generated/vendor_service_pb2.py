# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: vendor_service.proto
# Protobuf Python Version: 6.30.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    6,
    30,
    0,
    '',
    'vendor_service.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14vendor_service.proto\x12\x06vendor\x1a\x1cgoogle/protobuf/struct.proto\"0\n\x17GetAPIConfigByIDRequest\x12\x15\n\rapi_config_id\x18\x01 \x01(\t\"H\n\x18GetApiConfigByIDResponse\x12,\n\napi_config\x18\x01 \x01(\x0b\x32\x18.vendor.APIConfiguration\"5\n\x16\x43ommandTemplateRequest\x12\x1b\n\x13\x63ommand_template_id\x18\x01 \x01(\t\"O\n\x1aGetCommandTemplateResponse\x12\x31\n\x10\x63ommand_template\x18\x01 \x01(\x0b\x32\x17.vendor.CommandTemplate\"\"\n\rDeviceRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t\"3\n\x11GetDeviceResponse\x12\x1e\n\x06\x64\x65vice\x18\x01 \x01(\x0b\x32\x0e.vendor.Device\"@\n\x15\x43ommandContextRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x12\x14\n\x0c\x63ommand_type\x18\x02 \x01(\t\"\xc0\x01\n\x0e\x43ommandContext\x12\x1e\n\x06\x64\x65vice\x18\x01 \x01(\x0b\x32\x0e.vendor.Device\x12,\n\napi_config\x18\x02 \x01(\x0b\x32\x18.vendor.APIConfiguration\x12\x31\n\x10\x63ommand_template\x18\x03 \x01(\x0b\x32\x17.vendor.CommandTemplate\x12-\n\x0e\x64\x65vice_command\x18\x04 \x01(\x0b\x32\x15.vendor.DeviceCommand\"\xe8\x03\n\x06\x44\x65vice\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\r\n\x05model\x18\x03 \x01(\t\x12\x15\n\rserial_number\x18\x04 \x01(\t\x12\x18\n\x10\x66irmware_version\x18\x05 \x01(\t\x12\x10\n\x08\x62\x61se_url\x18\x06 \x01(\t\x12\x11\n\tauth_type\x18\x07 \x01(\t\x12,\n\x0b\x61uth_config\x18\x08 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x31\n\x10headers_template\x18\t \x01(\x0b\x32\x17.google.protobuf.Struct\x12.\n\rbody_template\x18\n \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x30\n\x0fparams_template\x18\x0b \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x0f\n\x07timeout\x18\x0c \x01(\x05\x12\x13\n\x0bretry_count\x18\r \x01(\x05\x12\x13\n\x0bretry_delay\x18\x0e \x01(\x05\x12\x11\n\tvendor_id\x18\x0f \x01(\t\x12\x13\n\x0bvendor_name\x18\x10 \x01(\t\x12\x11\n\tis_active\x18\x11 \x01(\x08\x12\x12\n\ncreated_at\x18\x12 \x01(\t\x12\x12\n\nupdated_at\x18\x13 \x01(\t\"\x8a\x03\n\x10\x41PIConfiguration\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x10\n\x08\x62\x61se_url\x18\x05 \x01(\t\x12\x11\n\tauth_type\x18\x06 \x01(\t\x12,\n\x0b\x61uth_config\x18\x07 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x31\n\x10headers_template\x18\x08 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x0f\n\x07timeout\x18\t \x01(\x05\x12\x13\n\x0bretry_count\x18\n \x01(\x05\x12\x13\n\x0bretry_delay\x18\x0b \x01(\x05\x12\x11\n\tvendor_id\x18\x0c \x01(\t\x12\x13\n\x0bvendor_name\x18\r \x01(\t\x12\x11\n\tis_active\x18\x0e \x01(\x08\x12\x12\n\ncreated_by\x18\x0f \x01(\t\x12\x12\n\ncreated_at\x18\x10 \x01(\t\x12\x12\n\nupdated_at\x18\x11 \x01(\t\"\x9d\x03\n\x0f\x43ommandTemplate\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x14\n\x0c\x63ommand_type\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x0e\n\x06method\x18\x05 \x01(\t\x12\x14\n\x0curl_template\x18\x06 \x01(\t\x12.\n\rbody_template\x18\x07 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x31\n\x10headers_template\x18\x08 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x10\n\x08\x62\x61se_url\x18\t \x01(\t\x12\x0f\n\x07timeout\x18\n \x01(\x05\x12\x13\n\x0bretry_count\x18\x0b \x01(\x05\x12\x13\n\x0bretry_delay\x18\x0c \x01(\x05\x12\x17\n\x0frequired_params\x18\r \x03(\t\x12\x17\n\x0foptional_params\x18\x0e \x03(\t\x12\x15\n\rapi_config_id\x18\x0f \x01(\t\x12\x12\n\ncreated_at\x18\x10 \x01(\t\x12\x12\n\nupdated_at\x18\x11 \x01(\t\"\xf2\x01\n\rDeviceCommand\x12\n\n\x02id\x18\x01 \x01(\t\x12\x11\n\tdevice_id\x18\x02 \x01(\t\x12\x1b\n\x13\x63ommand_template_id\x18\x03 \x01(\t\x12\x14\n\x0c\x63ommand_type\x18\x04 \x01(\t\x12.\n\rcustom_params\x18\x05 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x12\n\nis_primary\x18\x06 \x01(\x08\x12\x10\n\x08priority\x18\x07 \x01(\x05\x12\x11\n\tis_active\x18\x08 \x01(\x08\x12\x12\n\ncreated_at\x18\t \x01(\t\x12\x12\n\nupdated_at\x18\n \x01(\t2\xcb\x02\n\rVendorService\x12J\n\x11GetCommandContext\x12\x1d.vendor.CommandContextRequest\x1a\x16.vendor.CommandContext\x12U\n\x10GetAPIConfigByID\x12\x1f.vendor.GetAPIConfigByIDRequest\x1a .vendor.GetApiConfigByIDResponse\x12X\n\x12GetCommandTemplate\x12\x1e.vendor.CommandTemplateRequest\x1a\".vendor.GetCommandTemplateResponse\x12=\n\tGetDevice\x12\x15.vendor.DeviceRequest\x1a\x19.vendor.GetDeviceResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'vendor_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_GETAPICONFIGBYIDREQUEST']._serialized_start=62
  _globals['_GETAPICONFIGBYIDREQUEST']._serialized_end=110
  _globals['_GETAPICONFIGBYIDRESPONSE']._serialized_start=112
  _globals['_GETAPICONFIGBYIDRESPONSE']._serialized_end=184
  _globals['_COMMANDTEMPLATEREQUEST']._serialized_start=186
  _globals['_COMMANDTEMPLATEREQUEST']._serialized_end=239
  _globals['_GETCOMMANDTEMPLATERESPONSE']._serialized_start=241
  _globals['_GETCOMMANDTEMPLATERESPONSE']._serialized_end=320
  _globals['_DEVICEREQUEST']._serialized_start=322
  _globals['_DEVICEREQUEST']._serialized_end=356
  _globals['_GETDEVICERESPONSE']._serialized_start=358
  _globals['_GETDEVICERESPONSE']._serialized_end=409
  _globals['_COMMANDCONTEXTREQUEST']._serialized_start=411
  _globals['_COMMANDCONTEXTREQUEST']._serialized_end=475
  _globals['_COMMANDCONTEXT']._serialized_start=478
  _globals['_COMMANDCONTEXT']._serialized_end=670
  _globals['_DEVICE']._serialized_start=673
  _globals['_DEVICE']._serialized_end=1161
  _globals['_APICONFIGURATION']._serialized_start=1164
  _globals['_APICONFIGURATION']._serialized_end=1558
  _globals['_COMMANDTEMPLATE']._serialized_start=1561
  _globals['_COMMANDTEMPLATE']._serialized_end=1974
  _globals['_DEVICECOMMAND']._serialized_start=1977
  _globals['_DEVICECOMMAND']._serialized_end=2219
  _globals['_VENDORSERVICE']._serialized_start=2222
  _globals['_VENDORSERVICE']._serialized_end=2553
# @@protoc_insertion_point(module_scope)
