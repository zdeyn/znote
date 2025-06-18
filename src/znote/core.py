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
        if context is None:
            context = {}
        typed_payload: TPayload = dict(payload)
        # Traverse MRO to trigger all ancestor subscriptions
        for note_type in type(self).__mro__:
            if note_type in _subscriptions:
                for handler, _filter in _subscriptions[note_type]:
                    # Cast handler/filter to correct type for static checking
                    typed_handler = cast(Handler[Any], handler)
                    typed_filter = cast(Optional[Filter[Any]], _filter)
                    if typed_filter is None or typed_filter(self, typed_payload, context):
                        if asyncio.iscoroutinefunction(typed_handler):
                            await typed_handler(self, typed_payload, context)
                        else:
                            typed_handler(self, typed_payload, context)

def subscribe(note_type: Type[T], _filter: Optional[Filter[T]] = None) -> Callable[[Handler[T]], Handler[T]]:
    """
    A decorator to subscribe a handler to a zNote type or any subclass.
    Ensures type safety: handler will only be called with the correct note type.
    """
    def decorator(func: Handler[T]) -> Handler[T]:
        if note_type not in _subscriptions:
            _subscriptions[note_type] = []
        # type: ignore is needed for Python runtime, but mypy/pylance will enforce correct handler signature
        _subscriptions[note_type].append((func, _filter))  # type: ignore
        return func
    return decorator

