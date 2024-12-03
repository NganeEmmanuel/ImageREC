from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ImageRequest(_message.Message):
    __slots__ = ("image_data", "user_id")
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    image_data: bytes
    user_id: str
    def __init__(self, image_data: _Optional[bytes] = ..., user_id: _Optional[str] = ...) -> None: ...

class ImageResponse(_message.Message):
    __slots__ = ("request_id",)
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    def __init__(self, request_id: _Optional[str] = ...) -> None: ...

class ResultRequest(_message.Message):
    __slots__ = ("request_id",)
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    def __init__(self, request_id: _Optional[str] = ...) -> None: ...

class ResultResponse(_message.Message):
    __slots__ = ("status", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: str
    result: str
    def __init__(self, status: _Optional[str] = ..., result: _Optional[str] = ...) -> None: ...

class ModelRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ModelResponse(_message.Message):
    __slots__ = ("model_names",)
    MODEL_NAMES_FIELD_NUMBER: _ClassVar[int]
    model_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, model_names: _Optional[_Iterable[str]] = ...) -> None: ...

class ModelDetailRequest(_message.Message):
    __slots__ = ("model_name",)
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    def __init__(self, model_name: _Optional[str] = ...) -> None: ...

class ModelDetailResponse(_message.Message):
    __slots__ = ("details",)
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    details: str
    def __init__(self, details: _Optional[str] = ...) -> None: ...
