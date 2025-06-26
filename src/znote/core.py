import asyncio
from pydantic import BaseModel
from typing import Dict, Type, Callable, List, Tuple, Optional, Any, TypeVar, Generic, cast

T = TypeVar('T', bound='zNote')
TContext = Dict[str, Any]
TPayload = Dict[str, Any]
Handler = Callable[[T, TPayload, TContext], Any]
Filter = Callable[[T, TPayload, TContext], bool]

# Subscription registry
_subscriptions: Dict[Type['zNote'], List[Tuple[Handler[Any], Optional[Filter[Any]]]]] = {}

class zNote(BaseModel):
    """
    The root message class for znote, based on pydantic's BaseModel.

    Example:
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote)
        ... def handler(note, payload, context):
        ...     return note.message
        >>> note = MyNote(message="Hello world")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit())
        >>> for response in emission:
        ...     print(response.result)
        Hello world
    """
    async def emit(self, *, context: Optional[TContext] = None, **payload: Any) -> Any:
        """
        Emit this note to subscribed handlers.
        Returns an Emission object for introspection, but you can ignore it if you wish.
        """
        from .dispatch import Dispatcher
        return await Dispatcher.emit(self, context=context, **payload)

def subscribe(note_type: Type[T], _filter: Optional[Filter[T]] = None) -> Callable[[Handler[T]], Handler[T]]:
    """
    A decorator to subscribe a handler to a zNote type or any subclass.
    Ensures type safety: handler will only be called with the correct note type.

    Example (decorator):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote)
        ... def handler(note, payload, context):
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
        >>> def handler(note, payload, context):
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
        >>> @subscribe(MyNote, lambda note, payload, context: payload.get('ok', False))
        ... def filtered(note, payload, context):
        ...     return "filtered handler!"
        >>> note = MyNote(message="test")
        >>> import asyncio
        >>> emission = asyncio.run(note.emit(ok=True))
        >>> for response in emission:
        ...     print(response.result)
        filtered handler!
        >>> emission = asyncio.run(note.emit(ok=False))
        >>> for response in emission:
        ...     print(response.result)
    """
    from .dispatch import Dispatcher
    return Dispatcher.subscribe(note_type, _filter)

