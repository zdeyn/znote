from typing import Dict, Type, Callable, List, Tuple, Optional, Any, TypeVar, Generic, cast
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import zNote

T = TypeVar('T', bound='zNote')
TContext = Dict[str, Any]
TPayload = Dict[str, Any]
Handler = Callable[[T, TPayload, TContext], Any]
Filter = Callable[[T, TPayload, TContext], bool]

class Dispatcher:
    class _Subscription:
        """
        For internal use only: represents a handler/filter pair for a note type.
        """
        def __init__(self, handler: Handler[Any], filter: Optional[Filter[Any]] = None):
            self.handler = handler
            self.filter = filter

    # Subscription registry
    _subscriptions: Dict[Type['zNote'], List[Tuple[Handler[Any], Optional[Filter[Any]]]]] = {}

    @classmethod
    async def dispatch(cls, note: 'zNote', *, context: Optional[TContext] = None, **payload: Any) -> None:
        if context is None:
            context = {}
        typed_payload: TPayload = dict(payload)
        for note_type in type(note).__mro__:
            if note_type in cls._subscriptions:
                for handler, filter in cls._subscriptions[note_type]:
                    typed_handler = cast(Handler[Any], handler)
                    typed_filter = cast(Optional[Filter[Any]], filter)
                    if typed_filter is None or typed_filter(note, typed_payload, context):
                        if asyncio.iscoroutinefunction(typed_handler):
                            await typed_handler(note, typed_payload, context)
                        else:
                            typed_handler(note, typed_payload, context)

    @classmethod
    def subscribe(cls, note_type: Type[T], filter: Optional[Filter[T]] = None) -> Callable[[Handler[T]], Handler[T]]:
        def decorator(func: Handler[T]) -> Handler[T]:
            if note_type not in cls._subscriptions:
                cls._subscriptions[note_type] = []
            cls._subscriptions[note_type].append((func, filter))  # type: ignore
            return func
        return decorator
