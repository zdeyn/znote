import pytest
from typing import Any, Dict
from unittest.mock import MagicMock
from znote import zNote, subscribe
from znote.dispatch import Dispatcher, Emission

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
