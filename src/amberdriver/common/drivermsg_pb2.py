# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: drivermsg.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='drivermsg.proto',
  package='amber',
  serialized_pb=_b('\n\x0f\x64rivermsg.proto\x12\x05\x61mber\"H\n\tDriverHdr\x12\x12\n\ndeviceType\x18\x01 \x01(\x05\x12\x10\n\x08\x64\x65viceID\x18\x02 \x01(\x05\x12\x15\n\tclientIDs\x18\x03 \x03(\x05\x42\x02\x10\x01\"\xd9\x01\n\tDriverMsg\x12&\n\x04type\x18\x02 \x02(\x0e\x32\x18.amber.DriverMsg.MsgType\x12\x0e\n\x06synNum\x18\x03 \x01(\r\x12\x0e\n\x06\x61\x63kNum\x18\x04 \x01(\r\x12\x13\n\x0blistenerNum\x18\x05 \x01(\r\"i\n\x07MsgType\x12\x08\n\x04\x44\x41TA\x10\x01\x12\x08\n\x04PING\x10\x02\x12\x08\n\x04PONG\x10\x03\x12\x0f\n\x0b\x43LIENT_DIED\x10\x04\x12\x0f\n\x0b\x44RIVER_DIED\x10\x05\x12\r\n\tSUBSCRIBE\x10\x06\x12\x0f\n\x0bUNSUBSCRIBE\x10\x07*\x04\x08\n\x10\x64*\x95\x01\n\nDeviceType\x12\x0b\n\x07NINEDOF\x10\x01\x12\x0c\n\x08ROBOCLAW\x10\x02\x12\r\n\tSTARGAZER\x10\x03\x12\n\n\x06HOKUYO\x10\x04\x12\t\n\x05\x44UMMY\x10\x05\x12\x0c\n\x08LOCATION\x10\x06\x12\x0b\n\x07MAESTRO\x10\x07\x12\x12\n\x0e\x44RIVE_TO_POINT\x10\x08\x12\x17\n\x13\x43OLLISION_AVOIDANCE\x10\tB.\n\x1dpl.edu.agh.amber.common.protoB\x0b\x43ommonProtoH\x01')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_DEVICETYPE = _descriptor.EnumDescriptor(
  name='DeviceType',
  full_name='amber.DeviceType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='NINEDOF', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ROBOCLAW', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STARGAZER', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='HOKUYO', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DUMMY', index=4, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LOCATION', index=5, number=6,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MAESTRO', index=6, number=7,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DRIVE_TO_POINT', index=7, number=8,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='COLLISION_AVOIDANCE', index=8, number=9,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=321,
  serialized_end=470,
)
_sym_db.RegisterEnumDescriptor(_DEVICETYPE)

DeviceType = enum_type_wrapper.EnumTypeWrapper(_DEVICETYPE)
NINEDOF = 1
ROBOCLAW = 2
STARGAZER = 3
HOKUYO = 4
DUMMY = 5
LOCATION = 6
MAESTRO = 7
DRIVE_TO_POINT = 8
COLLISION_AVOIDANCE = 9


_DRIVERMSG_MSGTYPE = _descriptor.EnumDescriptor(
  name='MsgType',
  full_name='amber.DriverMsg.MsgType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='DATA', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PING', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PONG', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CLIENT_DIED', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DRIVER_DIED', index=4, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SUBSCRIBE', index=5, number=6,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='UNSUBSCRIBE', index=6, number=7,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=207,
  serialized_end=312,
)
_sym_db.RegisterEnumDescriptor(_DRIVERMSG_MSGTYPE)


_DRIVERHDR = _descriptor.Descriptor(
  name='DriverHdr',
  full_name='amber.DriverHdr',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='deviceType', full_name='amber.DriverHdr.deviceType', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='deviceID', full_name='amber.DriverHdr.deviceID', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='clientIDs', full_name='amber.DriverHdr.clientIDs', index=2,
      number=3, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=26,
  serialized_end=98,
)


_DRIVERMSG = _descriptor.Descriptor(
  name='DriverMsg',
  full_name='amber.DriverMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='amber.DriverMsg.type', index=0,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='synNum', full_name='amber.DriverMsg.synNum', index=1,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ackNum', full_name='amber.DriverMsg.ackNum', index=2,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='listenerNum', full_name='amber.DriverMsg.listenerNum', index=3,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _DRIVERMSG_MSGTYPE,
  ],
  options=None,
  is_extendable=True,
  extension_ranges=[(10, 100), ],
  oneofs=[
  ],
  serialized_start=101,
  serialized_end=318,
)

_DRIVERMSG.fields_by_name['type'].enum_type = _DRIVERMSG_MSGTYPE
_DRIVERMSG_MSGTYPE.containing_type = _DRIVERMSG
DESCRIPTOR.message_types_by_name['DriverHdr'] = _DRIVERHDR
DESCRIPTOR.message_types_by_name['DriverMsg'] = _DRIVERMSG
DESCRIPTOR.enum_types_by_name['DeviceType'] = _DEVICETYPE

DriverHdr = _reflection.GeneratedProtocolMessageType('DriverHdr', (_message.Message,), dict(
  DESCRIPTOR = _DRIVERHDR,
  __module__ = 'drivermsg_pb2'
  # @@protoc_insertion_point(class_scope:amber.DriverHdr)
  ))
_sym_db.RegisterMessage(DriverHdr)

DriverMsg = _reflection.GeneratedProtocolMessageType('DriverMsg', (_message.Message,), dict(
  DESCRIPTOR = _DRIVERMSG,
  __module__ = 'drivermsg_pb2'
  # @@protoc_insertion_point(class_scope:amber.DriverMsg)
  ))
_sym_db.RegisterMessage(DriverMsg)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n\035pl.edu.agh.amber.common.protoB\013CommonProtoH\001'))
_DRIVERHDR.fields_by_name['clientIDs'].has_options = True
_DRIVERHDR.fields_by_name['clientIDs']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
# @@protoc_insertion_point(module_scope)
