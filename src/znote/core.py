import asyncio
from pydantic import BaseModel
from typing import Dict, Type, Callable, List, Tuple, Optional, Any, TypeVar, Generic, cast

T = TypeVar('T', bound='zNote')
TContext = Dict[str, Any]
TPayload = Dict[str, Any]
# Handler and Filter type hints for type checkers: allow 1-3 arguments
from typing import Callable, Any, Optional, Type, List, Tuple, Dict
Handler = Callable[..., Any]
Filter = Callable[..., bool]
# Subscription registry
_subscriptions: Dict[Type[Any], List[Tuple[Handler, Optional[Filter]]]] = {}

class zNote(BaseModel):
    """
    The root message class for znote, based on pydantic's BaseModel.

    Example:
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote)
        ... def handler(note):
        ...     return f"note only: {note.message}"
        >>> @subscribe(MyNote)
        ... def handler2(note, payload):
        ...     return f"payload: {payload.get('user', 'none')}"
        >>> @subscribe(MyNote)
        ... def handler3(note, payload, context):
        ...     return f"context: {context.get('flag', False)}"
        >>> note = MyNote(message="Hello world")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit(user='alice', context={'flag': True}))
        >>> for response in emission:
        ...     print(response.result)
        note only: Hello world
        payload: alice
        context: True

    Example (function):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> def handler(note):
        ...     return note.message
        >>> _ = subscribe(MyNote)(handler)
        >>> note = MyNote(message="yo")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        yo

    Example (with filter):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote, lambda note: note.message == 'test')
        ... def filtered(note):
        ...     return "filtered handler!"
        >>> note = MyNote(message="test")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        filtered handler!
        >>> note2 = MyNote(message="notest")
        >>> emission = asyncio.run(note2.emit())
        >>> for response in emission:
        ...     print(response.result)
    """
    async def emit(self, *, context: Optional[TContext] = None, **payload: Any) -> Any:
        """
        Emit this note to subscribed handlers.
        Returns an Emission object for introspection, but you can ignore it if you wish.
        """
        from .dispatch import Dispatcher
        return await Dispatcher.emit(self, context=context, **payload)

    def __repr__(self):
        # Show class name and all fields/values, e.g. MyNote(message='hi', count=2)
        field_str = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({field_str})"

    def __str__(self):
        # User-friendly: just call __repr__
        return self.__repr__()

def subscribe(note_type: type, _filter: Optional[Filter] = None) -> Callable[[Handler], Handler]:
    """
    A decorator to subscribe a handler to a zNote type or any subclass.
    Ensures type safety: handler will only be called with the correct note type.

    Example (decorator):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote)
        ... def handler(note):
        ...     return note.message
        >>> note = MyNote(message="hi")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        hi

    Example (function):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> def handler(note):
        ...     return note.message
        >>> _ = subscribe(MyNote)(handler)
        >>> note = MyNote(message="yo")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        yo

    Example (with filter):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote, lambda note: note.message == 'test')
        ... def filtered(note):
        ...     return "filtered handler!"
        >>> note = MyNote(message="test")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        filtered handler!
        >>> note2 = MyNote(message="notest")
        >>> emission = asyncio.run(note2.emit())
        >>> for response in emission:
        ...     print(response.result)
    """
    from .dispatch import Dispatcher
    return Dispatcher.subscribe(note_type, _filter)

