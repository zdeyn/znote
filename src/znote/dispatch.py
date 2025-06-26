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

class Emission:
    """
    Iterable of _Response objects, one per handler called during emit.

    Each _Response contains:
        - handler: the handler function
        - note: the note instance
        - payload: the payload dict
        - context: the context dict
        - result: the handler's return value (may be None)

    Example:
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     x: int
        >>> @subscribe(MyNote)
        ... def sync_handler(note, payload, context):
        ...     return f"sync:{note.x}"
        >>> @subscribe(MyNote)
        ... async def async_handler(note, payload, context):
        ...     return f"async:{note.x}"
        >>> import asyncio
        >>> note = MyNote(x=5)
        >>> emission = asyncio.run(Dispatcher.emit(note))
        >>> [r.result for r in emission]
        ['sync:5', 'async:5']
    """
    class _Response:
        """
        Represents a single handler call during emission.
        """
        def __init__(self, handler, note, payload, context, result):
            self.handler = handler
            self.note = note
            self.payload = payload
            self.context = context
            self.result = result
        def __repr__(self):
            return f"<Emission._Response handler={self.handler.__name__} result={self.result!r}>"
    def __init__(self, responses):
        self._responses = responses
    def __iter__(self):
        return iter(self._responses)
    def __len__(self):
        return len(self._responses)
    def __getitem__(self, idx):
        return self._responses[idx]

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
    def subscribe(cls, note_type: Type[T], filter: Optional[Filter[T]] = None) -> Callable[[Handler[T]], Handler[T]]:
        def decorator(func: Handler[T]) -> Handler[T]:
            if note_type not in cls._subscriptions:
                cls._subscriptions[note_type] = []
            cls._subscriptions[note_type].append((func, filter))  # type: ignore
            return func
        return decorator

    @classmethod
    async def emit(cls, note: 'zNote', *, context: Optional[TContext] = None, **payload: Any) -> Emission:
        """
        Returns an Emission object of _Response objects for all handler calls.
        Each _Response contains the handler, note, payload, context, and result (may be None).

        Example:
            >>> from znote import zNote, subscribe, Emission, Dispatcher
            >>> class MyNote(zNote):
            ...     x: int
            >>> @subscribe(MyNote)
            ... def sync_handler(note, payload, context):
            ...     return f"sync:{note.x}"
            >>> @subscribe(MyNote)
            ... async def async_handler(note, payload, context):
            ...     return f"async:{note.x}"
            >>> import asyncio
            >>> note = MyNote(x=5)
            >>> emission = asyncio.run(Dispatcher.emit(note))
            >>> sorted([r.result for r in emission if r.result is not None])
            ['async:5', 'sync:5']
            >>> all(isinstance(r, Emission._Response) for r in emission)
            True

        Filtering and payload:
            >>> class MyNote(zNote):
            ...     y: int
            >>> @subscribe(MyNote, lambda note, payload, ctx: payload.get('ok', False))
            ... def sync_handler(note, payload, context):
            ...     return f"sync:{note.y}:{payload.get('ok')}"
            >>> @subscribe(MyNote)
            ... async def async_handler(note, payload, context):
            ...     return f"async:{note.y}"
            >>> note = MyNote(y=7)
            >>> emission = asyncio.run(Dispatcher.emit(note, ok=True))
            >>> sorted([r.result for r in emission if r.result is not None])
            ['async:7', 'sync:7:True']
            >>> emission2 = asyncio.run(Dispatcher.emit(note, ok=False))
            >>> [r.result for r in emission2 if r.result is not None]
            ['async:7']

        No handlers:
            >>> class MyNote(zNote):
            ...     pass
            >>> note = MyNote()
            >>> emission = asyncio.run(Dispatcher.emit(note))
            >>> all(r.result is None for r in emission)
            True
        """
        if context is None:
            context = {}
        typed_payload: TPayload = dict(payload)
        async_calls = []
        sync_responses = []
        for note_type in type(note).__mro__:
            if note_type in cls._subscriptions:
                for handler, filter in cls._subscriptions[note_type]:
                    typed_handler = cast(Handler[Any], handler)
                    typed_filter = cast(Optional[Filter[Any]], filter)
                    if typed_filter is None or typed_filter(note, typed_payload, context):
                        if asyncio.iscoroutinefunction(typed_handler):
                            async_calls.append((typed_handler, note, typed_payload, context))
                        else:
                            result = typed_handler(note, typed_payload, context)
                            sync_responses.append(Emission._Response(typed_handler, note, typed_payload, context, result))
        async_responses = []
        if async_calls:
            results = await asyncio.gather(*(h(n, p, c) for h, n, p, c in async_calls))
            for (handler, note, payload, context), result in zip(async_calls, results):
                async_responses.append(Emission._Response(handler, note, payload, context, result))
        return Emission(sync_responses + async_responses)
