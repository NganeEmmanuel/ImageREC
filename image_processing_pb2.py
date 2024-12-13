# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: image_processing.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'image_processing.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x16image_processing.proto\"D\n\x0fUserCredentials\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x10\n\x08password\x18\x03 \x01(\t\"B\n\x0cImageRequest\x12\x1e\n\x04user\x18\x01 \x01(\x0b\x32\x10.UserCredentials\x12\x12\n\nimage_data\x18\x02 \x01(\x0c\"#\n\rImageResponse\x12\x12\n\nrequest_id\x18\x01 \x01(\t\"B\n\x0cQueryRequest\x12\x1e\n\x04user\x18\x01 \x01(\x0b\x32\x10.UserCredentials\x12\x12\n\nrequest_id\x18\x02 \x01(\t\"0\n\x0eResultResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0e\n\x06result\x18\x02 \x01(\t\"F\n\x10ReprocessRequest\x12\x1e\n\x04user\x18\x01 \x01(\x0b\x32\x10.UserCredentials\x12\x12\n\nrequest_id\x18\x02 \x01(\t\"9\n\x17ReprocessResultResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0e\n\x06result\x18\x02 \x01(\t\".\n\x0cModelRequest\x12\x1e\n\x04user\x18\x01 \x01(\x0b\x32\x10.UserCredentials\"F\n\tModelInfo\x12\x12\n\nmodel_name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x10\n\x08\x61\x63\x63uracy\x18\x03 \x01(\x01\"H\n\x12ModelDetailRequest\x12\x1e\n\x04user\x18\x01 \x01(\x0b\x32\x10.UserCredentials\x12\x12\n\nmodel_name\x18\x02 \x01(\t\"H\n\x0bModelDetail\x12\x12\n\nmodel_name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x10\n\x08\x61\x63\x63uracy\x18\x03 \x01(\x01\"\"\n\x0c\x43hunkRequest\x12\x12\n\nchunk_data\x18\x01 \x01(\x0c\"2\n\rChunkResponse\x12\x0e\n\x06result\x18\x01 \x01(\t\x12\x11\n\tworker_id\x18\x02 \x01(\t\"\x0f\n\rHealthRequest\" \n\x0eHealthResponse\x12\x0e\n\x06status\x18\x01 \x01(\t2\x8c\x02\n\rMasterService\x12-\n\x0cProcessImage\x12\r.ImageRequest\x1a\x0e.ImageResponse\x12=\n\x0eReprocessImage\x12\x11.ReprocessRequest\x1a\x18.ReprocessResultResponse\x12-\n\x0bQueryResult\x12\r.QueryRequest\x1a\x0f.ResultResponse\x12(\n\tGetModels\x12\r.ModelRequest\x1a\n.ModelInfo0\x01\x12\x34\n\x0fGetModelDetails\x12\x13.ModelDetailRequest\x1a\x0c.ModelDetail2n\n\rWorkerService\x12-\n\x0cProcessChunk\x12\r.ChunkRequest\x1a\x0e.ChunkResponse\x12.\n\x0bHealthCheck\x12\x0e.HealthRequest\x1a\x0f.HealthResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'image_processing_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_USERCREDENTIALS']._serialized_start=26
  _globals['_USERCREDENTIALS']._serialized_end=94
  _globals['_IMAGEREQUEST']._serialized_start=96
  _globals['_IMAGEREQUEST']._serialized_end=162
  _globals['_IMAGERESPONSE']._serialized_start=164
  _globals['_IMAGERESPONSE']._serialized_end=199
  _globals['_QUERYREQUEST']._serialized_start=201
  _globals['_QUERYREQUEST']._serialized_end=267
  _globals['_RESULTRESPONSE']._serialized_start=269
  _globals['_RESULTRESPONSE']._serialized_end=317
  _globals['_REPROCESSREQUEST']._serialized_start=319
  _globals['_REPROCESSREQUEST']._serialized_end=389
  _globals['_REPROCESSRESULTRESPONSE']._serialized_start=391
  _globals['_REPROCESSRESULTRESPONSE']._serialized_end=448
  _globals['_MODELREQUEST']._serialized_start=450
  _globals['_MODELREQUEST']._serialized_end=496
  _globals['_MODELINFO']._serialized_start=498
  _globals['_MODELINFO']._serialized_end=568
  _globals['_MODELDETAILREQUEST']._serialized_start=570
  _globals['_MODELDETAILREQUEST']._serialized_end=642
  _globals['_MODELDETAIL']._serialized_start=644
  _globals['_MODELDETAIL']._serialized_end=716
  _globals['_CHUNKREQUEST']._serialized_start=718
  _globals['_CHUNKREQUEST']._serialized_end=752
  _globals['_CHUNKRESPONSE']._serialized_start=754
  _globals['_CHUNKRESPONSE']._serialized_end=804
  _globals['_HEALTHREQUEST']._serialized_start=806
  _globals['_HEALTHREQUEST']._serialized_end=821
  _globals['_HEALTHRESPONSE']._serialized_start=823
  _globals['_HEALTHRESPONSE']._serialized_end=855
  _globals['_MASTERSERVICE']._serialized_start=858
  _globals['_MASTERSERVICE']._serialized_end=1126
  _globals['_WORKERSERVICE']._serialized_start=1128
  _globals['_WORKERSERVICE']._serialized_end=1238
# @@protoc_insertion_point(module_scope)
