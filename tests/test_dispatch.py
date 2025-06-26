import pytest
from typing import Any, Dict
from znote import zNote, subscribe

# No need for @pytest.mark.asyncio since these are not async functions

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
    # There may be more than one handler, but at least one should match our handler
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
