# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: drive_to_point.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from amberdriver.common import drivermsg_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='drive_to_point.proto',
  package='amber.drive_to_point_proto',
  serialized_pb=_b('\n\x14\x64rive_to_point.proto\x12\x1a\x61mber.drive_to_point_proto\x1a\x0f\x64rivermsg.proto\"N\n\x07Targets\x12\x16\n\nlongitudes\x18\x01 \x03(\x01\x42\x02\x10\x01\x12\x15\n\tlatitudes\x18\x02 \x03(\x01\x42\x02\x10\x01\x12\x14\n\x08radiuses\x18\x03 \x03(\x01\x42\x02\x10\x01\"L\n\x08Location\x12\t\n\x01x\x18\x01 \x01(\x01\x12\t\n\x01y\x18\x02 \x01(\x01\x12\t\n\x01p\x18\x03 \x01(\x01\x12\x0c\n\x04\x61lfa\x18\x04 \x01(\x01\x12\x11\n\ttimeStamp\x18\x05 \x01(\x01\"!\n\rConfiguration\x12\x10\n\x08maxSpeed\x18\x01 \x01(\x01:$\n\nsetTargets\x12\x10.amber.DriverMsg\x18P \x01(\x08:\'\n\rgetNextTarget\x12\x10.amber.DriverMsg\x18Q \x01(\x08:(\n\x0egetNextTargets\x12\x10.amber.DriverMsg\x18R \x01(\x08:*\n\x10getVisitedTarget\x12\x10.amber.DriverMsg\x18S \x01(\x08:+\n\x11getVisitedTargets\x12\x10.amber.DriverMsg\x18T \x01(\x08:F\n\x07targets\x12\x10.amber.DriverMsg\x18U \x01(\x0b\x32#.amber.drive_to_point_proto.Targets:H\n\x08location\x12\x10.amber.DriverMsg\x18V \x01(\x0b\x32$.amber.drive_to_point_proto.Location:*\n\x10getConfiguration\x12\x10.amber.DriverMsg\x18W \x01(\x08:R\n\rconfiguration\x12\x10.amber.DriverMsg\x18X \x01(\x0b\x32).amber.drive_to_point_proto.ConfigurationB8\n#pl.edu.agh.amber.drivetopoint.protoB\x11\x44riveToPointProto')
  ,
  dependencies=[drivermsg_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


SETTARGETS_FIELD_NUMBER = 80
setTargets = _descriptor.FieldDescriptor(
  name='setTargets', full_name='amber.drive_to_point_proto.setTargets', index=0,
  number=80, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
GETNEXTTARGET_FIELD_NUMBER = 81
getNextTarget = _descriptor.FieldDescriptor(
  name='getNextTarget', full_name='amber.drive_to_point_proto.getNextTarget', index=1,
  number=81, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
GETNEXTTARGETS_FIELD_NUMBER = 82
getNextTargets = _descriptor.FieldDescriptor(
  name='getNextTargets', full_name='amber.drive_to_point_proto.getNextTargets', index=2,
  number=82, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
GETVISITEDTARGET_FIELD_NUMBER = 83
getVisitedTarget = _descriptor.FieldDescriptor(
  name='getVisitedTarget', full_name='amber.drive_to_point_proto.getVisitedTarget', index=3,
  number=83, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
GETVISITEDTARGETS_FIELD_NUMBER = 84
getVisitedTargets = _descriptor.FieldDescriptor(
  name='getVisitedTargets', full_name='amber.drive_to_point_proto.getVisitedTargets', index=4,
  number=84, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
TARGETS_FIELD_NUMBER = 85
targets = _descriptor.FieldDescriptor(
  name='targets', full_name='amber.drive_to_point_proto.targets', index=5,
  number=85, type=11, cpp_type=10, label=1,
  has_default_value=False, default_value=None,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
LOCATION_FIELD_NUMBER = 86
location = _descriptor.FieldDescriptor(
  name='location', full_name='amber.drive_to_point_proto.location', index=6,
  number=86, type=11, cpp_type=10, label=1,
  has_default_value=False, default_value=None,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
GETCONFIGURATION_FIELD_NUMBER = 87
getConfiguration = _descriptor.FieldDescriptor(
  name='getConfiguration', full_name='amber.drive_to_point_proto.getConfiguration', index=7,
  number=87, type=8, cpp_type=7, label=1,
  has_default_value=False, default_value=False,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)
CONFIGURATION_FIELD_NUMBER = 88
configuration = _descriptor.FieldDescriptor(
  name='configuration', full_name='amber.drive_to_point_proto.configuration', index=8,
  number=88, type=11, cpp_type=10, label=1,
  has_default_value=False, default_value=None,
  message_type=None, enum_type=None, containing_type=None,
  is_extension=True, extension_scope=None,
  options=None)


_TARGETS = _descriptor.Descriptor(
  name='Targets',
  full_name='amber.drive_to_point_proto.Targets',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='longitudes', full_name='amber.drive_to_point_proto.Targets.longitudes', index=0,
      number=1, type=1, cpp_type=5, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))),
    _descriptor.FieldDescriptor(
      name='latitudes', full_name='amber.drive_to_point_proto.Targets.latitudes', index=1,
      number=2, type=1, cpp_type=5, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))),
    _descriptor.FieldDescriptor(
      name='radiuses', full_name='amber.drive_to_point_proto.Targets.radiuses', index=2,
      number=3, type=1, cpp_type=5, label=3,
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
  serialized_start=69,
  serialized_end=147,
)


_LOCATION = _descriptor.Descriptor(
  name='Location',
  full_name='amber.drive_to_point_proto.Location',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='amber.drive_to_point_proto.Location.x', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='y', full_name='amber.drive_to_point_proto.Location.y', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='p', full_name='amber.drive_to_point_proto.Location.p', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='alfa', full_name='amber.drive_to_point_proto.Location.alfa', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timeStamp', full_name='amber.drive_to_point_proto.Location.timeStamp', index=4,
      number=5, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
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
  serialized_start=149,
  serialized_end=225,
)


_CONFIGURATION = _descriptor.Descriptor(
  name='Configuration',
  full_name='amber.drive_to_point_proto.Configuration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='maxSpeed', full_name='amber.drive_to_point_proto.Configuration.maxSpeed', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
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
  serialized_start=227,
  serialized_end=260,
)

DESCRIPTOR.message_types_by_name['Targets'] = _TARGETS
DESCRIPTOR.message_types_by_name['Location'] = _LOCATION
DESCRIPTOR.message_types_by_name['Configuration'] = _CONFIGURATION
DESCRIPTOR.extensions_by_name['setTargets'] = setTargets
DESCRIPTOR.extensions_by_name['getNextTarget'] = getNextTarget
DESCRIPTOR.extensions_by_name['getNextTargets'] = getNextTargets
DESCRIPTOR.extensions_by_name['getVisitedTarget'] = getVisitedTarget
DESCRIPTOR.extensions_by_name['getVisitedTargets'] = getVisitedTargets
DESCRIPTOR.extensions_by_name['targets'] = targets
DESCRIPTOR.extensions_by_name['location'] = location
DESCRIPTOR.extensions_by_name['getConfiguration'] = getConfiguration
DESCRIPTOR.extensions_by_name['configuration'] = configuration

Targets = _reflection.GeneratedProtocolMessageType('Targets', (_message.Message,), dict(
  DESCRIPTOR = _TARGETS,
  __module__ = 'drive_to_point_pb2'
  # @@protoc_insertion_point(class_scope:amber.drive_to_point_proto.Targets)
  ))
_sym_db.RegisterMessage(Targets)

Location = _reflection.GeneratedProtocolMessageType('Location', (_message.Message,), dict(
  DESCRIPTOR = _LOCATION,
  __module__ = 'drive_to_point_pb2'
  # @@protoc_insertion_point(class_scope:amber.drive_to_point_proto.Location)
  ))
_sym_db.RegisterMessage(Location)

Configuration = _reflection.GeneratedProtocolMessageType('Configuration', (_message.Message,), dict(
  DESCRIPTOR = _CONFIGURATION,
  __module__ = 'drive_to_point_pb2'
  # @@protoc_insertion_point(class_scope:amber.drive_to_point_proto.Configuration)
  ))
_sym_db.RegisterMessage(Configuration)

drivermsg_pb2.DriverMsg.RegisterExtension(setTargets)
drivermsg_pb2.DriverMsg.RegisterExtension(getNextTarget)
drivermsg_pb2.DriverMsg.RegisterExtension(getNextTargets)
drivermsg_pb2.DriverMsg.RegisterExtension(getVisitedTarget)
drivermsg_pb2.DriverMsg.RegisterExtension(getVisitedTargets)
targets.message_type = _TARGETS
drivermsg_pb2.DriverMsg.RegisterExtension(targets)
location.message_type = _LOCATION
drivermsg_pb2.DriverMsg.RegisterExtension(location)
drivermsg_pb2.DriverMsg.RegisterExtension(getConfiguration)
configuration.message_type = _CONFIGURATION
drivermsg_pb2.DriverMsg.RegisterExtension(configuration)

DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n#pl.edu.agh.amber.drivetopoint.protoB\021DriveToPointProto'))
_TARGETS.fields_by_name['longitudes'].has_options = True
_TARGETS.fields_by_name['longitudes']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
_TARGETS.fields_by_name['latitudes'].has_options = True
_TARGETS.fields_by_name['latitudes']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
_TARGETS.fields_by_name['radiuses'].has_options = True
_TARGETS.fields_by_name['radiuses']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
# @@protoc_insertion_point(module_scope)
