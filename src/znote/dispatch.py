from typing import Dict, Type, Callable, List, Tuple, Optional
import asyncio
from typing import TYPE_CHECKING
import inspect

# Handler and Filter type hints for type checkers: allow 1-3 arguments
from typing import Callable, Any, Optional, Type, List, Tuple, Dict
Handler = Callable[..., Any]
Filter = Callable[..., bool]
TContext = Dict[str, Any]
TPayload = Dict[str, Any]
T = Any

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
        def __init__(self, handler: Handler, filter: Optional[Filter] = None):
            self.handler = handler
            self.filter = filter

    # Subscription registry
    _subscriptions: Dict[Type[Any], List[Tuple[Handler, Optional[Filter]]]] = {}

    @classmethod
    def subscribe(cls, note_type: Type[Any], filter: Optional[Filter] = None) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            if note_type not in cls._subscriptions:
                cls._subscriptions[note_type] = []
            cls._subscriptions[note_type].append((func, filter))
            return func
        return decorator

    @classmethod
    async def emit(cls, note: Any, *, context: Optional[Dict[str, Any]] = None, **payload: Any) -> Emission:
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
        typed_payload: Dict[str, Any] = dict(payload)
        async_calls = []
        sync_responses = []
        seen_handlers = set()
        for note_type in type(note).__mro__:
            if note_type in cls._subscriptions:
                for handler, filter in cls._subscriptions[note_type]:
                    if handler in seen_handlers:
                        continue
                    seen_handlers.add(handler)
                    # Prepare args for handler/filter
                    handler_args = (note, typed_payload, context)
                    filter_args = (note, typed_payload, context) if filter is not None else None
                    # Use inspect to determine how many args to pass
                    def get_args_to_pass(fn, all_args):
                        sig = inspect.signature(fn)
                        n = len(sig.parameters)
                        # Defensive: always return a tuple of the right length
                        return tuple(all_args[:n])
                    # Check filter
                    if filter is None or filter(*get_args_to_pass(filter, filter_args)):
                        if asyncio.iscoroutinefunction(handler):
                            async_calls.append((handler, get_args_to_pass(handler, handler_args)))
                        else:
                            result = handler(*get_args_to_pass(handler, handler_args))
                            sync_responses.append(Emission._Response(handler, note, typed_payload, context, result))
        async_responses = []
        if async_calls:
            results = await asyncio.gather(*(h(*args) for h, args in async_calls))
            for (handler, args), result in zip(async_calls, results):
                async_responses.append(Emission._Response(handler, args[0], args[1] if len(args) > 1 else {}, args[2] if len(args) > 2 else {}, result))
        return Emission(sync_responses + async_responses)

    @classmethod
    def clear_subscriptions(cls):
        """Remove all subscriptions (for test isolation or dynamic reloading)."""
        cls._subscriptions.clear()
