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
        - payload: the payload dict (attachments/entities for the note)
        - context: the context dict (internal storage, scratch-space, etc)
        - result: the handler's return value (may be None)

    Example:
        >>> from znote import zNote, subscribe
        >>> class MyNote(zNote):
        ...     x: int
        >>> @subscribe(MyNote)
        ... def sync_handler(note, payload, context):
        ...     # payload is for attachments/entities (e.g. user, files)
        ...     # context is for internal scratch-space, etc
        ...     return f"sync:{note.x}, user={payload.get('user')}, flag={context.get('flag')}"
        >>> import asyncio
        >>> note = MyNote(x=5)
        >>> emission = asyncio.run(Dispatcher.emit(note, user='bob', context={'flag': True}))
        >>> for r in emission:
        ...     print(r)
        Response from sync_handler on MyNote(x=5): 'sync:5, user=bob, flag=True'
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
            # Show handler, note details, and result
            note_str = repr(self.note)
            return (f"<Response handler={self.handler.__name__} note={note_str} result={self.result!r}>")
        def __str__(self):
            note_str = repr(self.note)
            return (f"Response from {self.handler.__name__} on {note_str}: {self.result!r}")

    def __init__(self, responses):
        self._responses = responses
    def __iter__(self):
        return iter(self._responses)
    def __len__(self):
        return len(self._responses)
    def __getitem__(self, idx):
        return self._responses[idx]
    def __repr__(self):
        # Show summary: Emission(len=2, results=[...]) and note details for each response
        return (f"Emission(len={len(self)}, responses=[" + ", ".join(repr(r) for r in self._responses) + "])")
    def __str__(self):
        # Pretty print all responses
        return "\n".join(str(r) for r in self._responses)

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
            ...     # payload is for attachments/entities (e.g. user, files)
            ...     # context is for internal scratch-space, etc
            ...     return f"sync:{note.x}, user={payload.get('user')}, flag={context.get('flag')}"
            >>> import asyncio
            >>> note = MyNote(x=5)
            >>> emission = asyncio.run(Dispatcher.emit(note, user='bob', context={'flag': True}))
            >>> for r in emission:
            ...     print(r)
            Response from sync_handler on MyNote(x=5): 'sync:5, user=bob, flag=True'

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
            >>> for r in emission:
            ...     print(r)
            Response from sync_handler on MyNote(y=7): 'sync:7:True'
            Response from async_handler on MyNote(y=7): 'async:7'
            >>> emission2 = asyncio.run(Dispatcher.emit(note, ok=False))
            >>> for r in emission2:
            ...     print(r)
            Response from async_handler on MyNote(y=7): 'async:7'

        No handlers:
            >>> class MyNote(zNote):
            ...     pass
            >>> note = MyNote()
            >>> emission = asyncio.run(Dispatcher.emit(note))
            >>> print(emission)
            
        """
        if context is None:
            context = {}
        typed_payload: TPayload = dict(payload)
        async_calls = []
        sync_responses = []
        seen_handlers = set()
        for note_type in type(note).__mro__:
            if note_type in cls._subscriptions:
                for handler, filter in cls._subscriptions[note_type]:
                    if handler in seen_handlers:
                        continue
                    seen_handlers.add(handler)
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

    @classmethod
    def clear_subscriptions(cls):
        """Remove all subscriptions (for test isolation or dynamic reloading)."""
        cls._subscriptions.clear()
