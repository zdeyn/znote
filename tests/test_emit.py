import pytest
from typing import Any, Dict
from znote import zNote, subscribe
from znote.dispatch import Dispatcher, Emission

def test_simple_subscription_emit():
    class MyNote(zNote):
        greeting: str
    called = []
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["modified"] = True
        called.append((note, payload, context))
    import asyncio
    emission = asyncio.run(MyNote(greeting="hello").emit(foo={"test-key": "test-value"}))
    assert any(response.note.greeting == "hello" and response.payload["foo"] == {"test-key": "test-value"} and response.context["modified"] is True for response in emission)
    assert any(c[0].greeting == "hello" for c in called)

def test_filtered_subscription_emit():
    class MyNote(zNote):
        id: int
    called = []
    @subscribe(MyNote)
    async def always(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["always_count"] = context.get("always_count", 0) + 1
        called.append(("always", note.id, payload["count"], dict(context)))
    @subscribe(MyNote, lambda note, payload, context: payload["count"] == 2)
    async def filtered(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["filtered_count"] = context.get("filtered_count", 0) + 1
        called.append(("filtered", note.id, payload["count"], dict(context)))
    import asyncio
    for i in range(3):
        emission = asyncio.run(MyNote(id=i).emit(count=i))
    always_calls = [c for c in called if c[0] == "always"]
    filtered_calls = [c for c in called if c[0] == "filtered"]
    assert len(always_calls) == 3
    assert len(filtered_calls) == 1
    assert filtered_calls[0][1] == 2
    assert filtered_calls[0][2] == 2
    assert filtered_calls[0][3]["filtered_count"] == 1

def test_context_propagation_emit():
    class MyNote(zNote):
        data: str
    initial_context: Dict[str, Any] = {"user_id": "test_user"}
    called = []
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        called.append(context)
    import asyncio
    emission = asyncio.run(MyNote(data="hello").emit(context=initial_context))
    assert any(c == initial_context for c in called)
    assert any(response.context == initial_context for response in emission)

@pytest.mark.asyncio
async def test_emit_collects_all_handler_responses() -> None:
    """
    Emission returns an iterable of _Response objects, one per handler.

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
    """
    class MyNote(zNote):
        x: int
    @subscribe(MyNote)
    def sync_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"sync:{note.x}"
    @subscribe(MyNote)
    async def async_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"async:{note.x}"
    note = MyNote(x=5)
    emission = await Dispatcher.emit(note)
    results = sorted([r.result for r in emission if r.result is not None])
    assert results == ["async:5", "sync:5"]
    assert all(isinstance(r, Emission._Response) for r in emission)

@pytest.mark.asyncio
async def test_emit_with_filters_and_payload() -> None:
    """
    >>> class MyNote(zNote):
    ...     y: int
    >>> @subscribe(MyNote, lambda note, payload, ctx: payload.get('ok', False))
    ... def sync_handler(note, payload, context):
    ...     return f"sync:{note.y}:{payload.get('ok')}"
    >>> @subscribe(MyNote)
    ... async def async_handler(note, payload, context):
    ...     return f"async:{note.y}"
    >>> import asyncio
    >>> note = MyNote(y=7)
    >>> emission = asyncio.run(Dispatcher.emit(note, ok=True))
    >>> sorted([r.result for r in emission if r.result is not None])
    ['async:7', 'sync:7:True']
    >>> emission2 = asyncio.run(Dispatcher.emit(note, ok=False))
    >>> [r.result for r in emission2 if r.result is not None]
    ['async:7']
    """
    class MyNote(zNote):
        y: int
    @subscribe(MyNote, lambda note, payload, ctx: payload.get("ok", False))
    def sync_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"sync:{note.y}:{payload.get('ok')}"
    @subscribe(MyNote)
    async def async_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"async:{note.y}"
    note = MyNote(y=7)
    emission1 = await Dispatcher.emit(note, ok=True)
    results1 = sorted([r.result for r in emission1 if r.result is not None])
    assert results1 == ["async:7", "sync:7:True"]
    emission2 = await Dispatcher.emit(note, ok=False)
    results2 = [r.result for r in emission2 if r.result is not None]
    assert results2 == ["async:7"]

@pytest.mark.asyncio
async def test_emit_empty_if_no_handlers() -> None:
    """
    >>> class MyNote(zNote):
    ...     pass
    >>> import asyncio
    >>> note = MyNote()
    >>> emission = asyncio.run(Dispatcher.emit(note))
    >>> all(r.result is None for r in emission)
    True
    """
    class MyNote(zNote):
        pass
    note = MyNote()
    emission = await Dispatcher.emit(note)
    assert all(r.result is None for r in emission)
