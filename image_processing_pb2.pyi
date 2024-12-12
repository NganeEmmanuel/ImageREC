from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UserCredentials(_message.Message):
    __slots__ = ("email", "username", "password")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    email: str
    username: str
    password: str
    def __init__(self, email: _Optional[str] = ..., username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class ImageRequest(_message.Message):
    __slots__ = ("user", "image_data")
    USER_FIELD_NUMBER: _ClassVar[int]
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    image_data: bytes
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., image_data: _Optional[bytes] = ...) -> None: ...

class ImageResponse(_message.Message):
    __slots__ = ("request_id",)
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    def __init__(self, request_id: _Optional[str] = ...) -> None: ...

class QueryRequest(_message.Message):
    __slots__ = ("user", "request_id")
    USER_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    request_id: str
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., request_id: _Optional[str] = ...) -> None: ...

class ResultResponse(_message.Message):
    __slots__ = ("status", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: str
    result: str
    def __init__(self, status: _Optional[str] = ..., result: _Optional[str] = ...) -> None: ...

class ModelRequest(_message.Message):
    __slots__ = ("user",)
    USER_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ...) -> None: ...

class ModelInfo(_message.Message):
    __slots__ = ("model_name", "description", "accuracy")
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    description: str
    accuracy: float
    def __init__(self, model_name: _Optional[str] = ..., description: _Optional[str] = ..., accuracy: _Optional[float] = ...) -> None: ...

class ModelDetailRequest(_message.Message):
    __slots__ = ("user", "model_name")
    USER_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    model_name: str
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., model_name: _Optional[str] = ...) -> None: ...

class ModelDetail(_message.Message):
    __slots__ = ("model_name", "description", "accuracy")
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    description: str
    accuracy: float
    def __init__(self, model_name: _Optional[str] = ..., description: _Optional[str] = ..., accuracy: _Optional[float] = ...) -> None: ...

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
