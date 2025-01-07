from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

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

class ProcessImageRequest(_message.Message):
    __slots__ = ("user_id", "user", "images", "model_name", "action_type", "number_of_remote_images")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    IMAGES_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    ACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_REMOTE_IMAGES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    user: UserCredentials
    images: _containers.RepeatedCompositeFieldContainer[ImageData]
    model_name: str
    action_type: str
    number_of_remote_images: int
    def __init__(self, user_id: _Optional[str] = ..., user: _Optional[_Union[UserCredentials, _Mapping]] = ..., images: _Optional[_Iterable[_Union[ImageData, _Mapping]]] = ..., model_name: _Optional[str] = ..., action_type: _Optional[str] = ..., number_of_remote_images: _Optional[int] = ...) -> None: ...

class ImageData(_message.Message):
    __slots__ = ("image_data", "image_id", "image_url", "location")
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    IMAGE_ID_FIELD_NUMBER: _ClassVar[int]
    IMAGE_URL_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    image_data: bytes
    image_id: int
    image_url: str
    location: str
    def __init__(self, image_data: _Optional[bytes] = ..., image_id: _Optional[int] = ..., image_url: _Optional[str] = ..., location: _Optional[str] = ...) -> None: ...

class RemoteImageRequest(_message.Message):
    __slots__ = ("user", "image_url")
    USER_FIELD_NUMBER: _ClassVar[int]
    IMAGE_URL_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    image_url: str
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., image_url: _Optional[str] = ...) -> None: ...

class ProcessImageResponse(_message.Message):
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
    __slots__ = ("status", "result_data")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_DATA_FIELD_NUMBER: _ClassVar[int]
    status: str
    result_data: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, status: _Optional[str] = ..., result_data: _Optional[_Iterable[str]] = ...) -> None: ...

class EmptyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReprocessRequest(_message.Message):
    __slots__ = ("user", "request_id")
    USER_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    request_id: str
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., request_id: _Optional[str] = ...) -> None: ...

class ReprocessResultResponse(_message.Message):
    __slots__ = ("status", "request_id", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: str
    request_id: str
    message: str
    def __init__(self, status: _Optional[str] = ..., request_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ModelRequest(_message.Message):
    __slots__ = ("user",)
    USER_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ...) -> None: ...

class ModelInfo(_message.Message):
    __slots__ = ("model_name", "description", "version", "supported_actions", "accuracy")
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    description: str
    version: str
    supported_actions: str
    accuracy: float
    def __init__(self, model_name: _Optional[str] = ..., description: _Optional[str] = ..., version: _Optional[str] = ..., supported_actions: _Optional[str] = ..., accuracy: _Optional[float] = ...) -> None: ...

class ModelDetailRequest(_message.Message):
    __slots__ = ("user", "model_name")
    USER_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    user: UserCredentials
    model_name: str
    def __init__(self, user: _Optional[_Union[UserCredentials, _Mapping]] = ..., model_name: _Optional[str] = ...) -> None: ...

class ModelDetail(_message.Message):
    __slots__ = ("model_name", "description", "version", "supported_actions", "accuracy", "last_updated")
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATED_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    description: str
    version: str
    supported_actions: str
    accuracy: float
    last_updated: str
    def __init__(self, model_name: _Optional[str] = ..., description: _Optional[str] = ..., version: _Optional[str] = ..., supported_actions: _Optional[str] = ..., accuracy: _Optional[float] = ..., last_updated: _Optional[str] = ...) -> None: ...

class GetServicesResponse(_message.Message):
    __slots__ = ("service_names",)
    SERVICE_NAMES_FIELD_NUMBER: _ClassVar[int]
    service_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, service_names: _Optional[_Iterable[str]] = ...) -> None: ...

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

class RequestDataRespond(_message.Message):
    __slots__ = ("request_id", "request_status", "request_date")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_DATE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    request_status: str
    request_date: str
    def __init__(self, request_id: _Optional[str] = ..., request_status: _Optional[str] = ..., request_date: _Optional[str] = ...) -> None: ...

class WorkerRegistration(_message.Message):
    __slots__ = ("worker_id", "tag", "address")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    tag: str
    address: str
    def __init__(self, worker_id: _Optional[str] = ..., tag: _Optional[str] = ..., address: _Optional[str] = ...) -> None: ...

class RegistrationResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: str
    message: str
    def __init__(self, status: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class WorkerTagRequest(_message.Message):
    __slots__ = ("tag",)
    TAG_FIELD_NUMBER: _ClassVar[int]
    tag: str
    def __init__(self, tag: _Optional[str] = ...) -> None: ...

class WorkersResponse(_message.Message):
    __slots__ = ("workers",)
    WORKERS_FIELD_NUMBER: _ClassVar[int]
    workers: _containers.RepeatedCompositeFieldContainer[WorkerInfo]
    def __init__(self, workers: _Optional[_Iterable[_Union[WorkerInfo, _Mapping]]] = ...) -> None: ...

class WorkerInfo(_message.Message):
    __slots__ = ("worker_id", "address", "tag")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    address: str
    tag: str
    def __init__(self, worker_id: _Optional[str] = ..., address: _Optional[str] = ..., tag: _Optional[str] = ...) -> None: ...
