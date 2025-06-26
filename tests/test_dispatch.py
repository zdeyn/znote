import pytest
from typing import Any, Dict
from unittest.mock import MagicMock
from znote import zNote, subscribe

@pytest.mark.asyncio
async def test_simple_subscription_dispatch() -> None:
    class MyNote(zNote):
        greeting: str
    mock_callback: MagicMock = MagicMock()
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["modified"] = True
        mock_callback(note, payload, context)
    note: MyNote = MyNote(greeting="hello")
    await note.dispatch(foo={"test-key": "test-value"})
    mock_callback.assert_called_once()
    called_note, called_payload, called_context = mock_callback.call_args[0]
    assert isinstance(called_note, MyNote)
    assert called_note is note
    assert called_note.greeting == "hello"
    assert isinstance(called_payload, dict)
    assert "foo" in called_payload
    assert called_payload.get("foo") == {"test-key": "test-value"}
    assert isinstance(called_context, dict)
    assert "modified" in called_context
    assert called_context.get("modified", False) is True

@pytest.mark.asyncio
async def test_filtered_subscription() -> None:
    class MyNote(zNote):
        id: int
    mock_callback: MagicMock = MagicMock()
    results: list = []
    @subscribe(MyNote)
    async def my_always_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["always_count"] = context.get("always_count", 0) + 1
        mock_callback("always", note.id, payload["count"], dict(context))
        results.append(("always", note.id, payload["count"], dict(context)))
    @subscribe(MyNote, lambda note, payload, context: payload["count"] == 2)
    async def my_filtered_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        context["filtered_count"] = context.get("filtered_count", 0) + 1
        mock_callback("filtered", note.id, payload["count"], dict(context))
        results.append(("filtered", note.id, payload["count"], dict(context)))
    for i in range(3):
        note: MyNote = MyNote(id=i)
        await note.dispatch(count=i)
    assert mock_callback.call_count == 4
    assert len(results) == 4
    always_calls = [r for r in results if r[0] == "always"]
    assert len(always_calls) == 3
    for idx, call in enumerate(always_calls):
        handler, note_id, count, context = call
        assert handler == "always"
        assert note_id == idx
        assert count == idx
        assert context["always_count"] == 1
        assert "filtered_count" not in context
    filtered_calls = [r for r in results if r[0] == "filtered"]
    assert len(filtered_calls) == 1
    handler, note_id, count, context = filtered_calls[0]
    assert handler == "filtered"
    assert note_id == 2
    assert count == 2
    assert context["filtered_count"] == 1
    assert context.get("always_count") == 1 or context.get("always_count") is None

@pytest.mark.asyncio
async def test_context_propagation() -> None:
    class MyNote(zNote):
        data: str
    mock_callback: MagicMock = MagicMock()
    initial_context: Dict[str, Any] = {"user_id": "test_user"}
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        mock_callback(context)
    note: MyNote = MyNote(data="hello")
    await note.dispatch(context=initial_context)
    mock_callback.assert_called_once()
    called_context = mock_callback.call_args[0][0]
    assert called_context == initial_context
