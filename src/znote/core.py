import asyncio
from pydantic import BaseModel
from typing import Dict, Type, Callable, List, Tuple, Optional, Any, TypeVar, Generic, cast
from .dispatch import Dispatcher

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
        ...     print(note.message)
        >>> note = MyNote(message="Hello world")
        >>> import asyncio
        >>> asyncio.run(note.dispatch())
        Hello world
    """
    async def dispatch(self, *, context: Optional[TContext] = None, **payload: Any) -> None:
        """
        Dispatch this note to subscribed handlers.
        Allows user-supplied context, otherwise uses a fresh dict.
        Triggers all subscriptions for this note's class and its ancestors.
        """
        await Dispatcher.dispatch(self, context=context, **payload)

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
        ...     print(f"decorator: {note.message}")
        >>> note = MyNote(message="hi")
        >>> import asyncio
        >>> asyncio.run(note.dispatch())
        decorator: hi

    Example (function):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> def handler(note, payload, context):
        ...     print(f"function: {note.message}")
        >>> _ = subscribe(MyNote)(handler)
        >>> note = MyNote(message="yo")
        >>> import asyncio
        >>> asyncio.run(note.dispatch())
        function: yo

    Example (with filter):
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     message: str
        >>> @subscribe(MyNote, lambda note, payload, context: payload.get('ok', False))
        ... def filtered(note, payload, context):
        ...     print("filtered handler!")
        >>> note = MyNote(message="test")
        >>> import asyncio
        >>> asyncio.run(note.dispatch(ok=True))
        filtered handler!
        >>> asyncio.run(note.dispatch(ok=False))
    """
    return Dispatcher.subscribe(note_type, _filter)

