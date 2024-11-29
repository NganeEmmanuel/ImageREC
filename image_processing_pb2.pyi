from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageRequest(_message.Message):
    __slots__ = ("image_data",)
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    image_data: bytes
    def __init__(self, image_data: _Optional[bytes] = ...) -> None: ...

class ImageResponse(_message.Message):
    __slots__ = ("worker_responses",)
    WORKER_RESPONSES_FIELD_NUMBER: _ClassVar[int]
    worker_responses: _containers.RepeatedCompositeFieldContainer[ChunkResponse]
    def __init__(self, worker_responses: _Optional[_Iterable[_Union[ChunkResponse, _Mapping]]] = ...) -> None: ...

class ChunkRequest(_message.Message):
    __slots__ = ("chunk_data",)
    CHUNK_DATA_FIELD_NUMBER: _ClassVar[int]
    chunk_data: bytes
    def __init__(self, chunk_data: _Optional[bytes] = ...) -> None: ...

class ChunkResponse(_message.Message):
    __slots__ = ("result", "worker_id")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    result: str
    worker_id: str
    def __init__(self, result: _Optional[str] = ..., worker_id: _Optional[str] = ...) -> None: ...

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
