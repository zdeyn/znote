import pytest
from typing import Any, Dict, Callable
from unittest.mock import MagicMock
from znote import zNote, subscribe

# 1. Test basic zNote creation and attribute access
def test_znote_creation() -> None:
    """
    Test that a zNote can be created with data and that its attributes are accessible.
    This verifies the pydantic BaseModel integration.
    """
    class MyNote(zNote):
        name: str = "test"
        value: int = 10

    note: MyNote = MyNote()
    assert note.name == "test"
    assert note.value == 10

# 2. Test simple subscription and dispatch
@pytest.mark.asyncio
async def test_simple_subscription_dispatch() -> None:
    """
    Test that a simple subscription works and the callback is called upon dispatch.
    Uses a mock to verify the callback execution.
    """
    class MyNote(zNote):
        greeting: str

    mock_callback: MagicMock = MagicMock()

    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # we should modify/add to the context within the handler
        context["modified"] = True
        mock_callback(note, payload, context)

    note: MyNote = MyNote(greeting="hello")
    await note.dispatch(foo={"test-key": "test-value"}) # pass additional arbitrary data as payload

    mock_callback.assert_called_once()
    called_note, called_payload, called_context = mock_callback.call_args[0]

    # verify the correct note was passed to the callback
    assert isinstance(called_note, MyNote)    
    assert called_note is note
    assert called_note.greeting == "hello"

    # verify the payload contains the inline data
    assert isinstance(called_payload, dict)
    assert "foo" in called_payload    
    assert called_payload.get("foo") == {"test-key": "test-value"}

    # verify the context is passed correctly
    assert isinstance(called_context, dict)
    assert "modified" in called_context    
    assert called_context.get("modified", False) is True  # Check if context was modified in the handler

# 3. Test filtered subscription
@pytest.mark.asyncio
async def test_filtered_subscription() -> None:
    """
    Test that a subscription with a filter only triggers the callback when the filter matches.
    The 'always' handler should be called for every dispatch, and the 'filtered' handler only when the filter matches.
    The context should be updated independently for each handler call.
    """
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

    # There should be 3 dispatches, but 4 handler calls (3 always, 1 filtered)
    assert mock_callback.call_count == 4
    assert len(results) == 4

    # Check the always handler calls
    always_calls = [r for r in results if r[0] == "always"]
    assert len(always_calls) == 3
    for idx, call in enumerate(always_calls):
        handler, note_id, count, context = call
        assert handler == "always"
        assert note_id == idx
        assert count == idx
        assert context["always_count"] == 1
        assert "filtered_count" not in context

    # Check the filtered handler call (should be only for count==2)
    filtered_calls = [r for r in results if r[0] == "filtered"]
    assert len(filtered_calls) == 1
    handler, note_id, count, context = filtered_calls[0]
    assert handler == "filtered"
    assert note_id == 2
    assert count == 2
    assert context["filtered_count"] == 1
    assert context.get("always_count") == 1 or context.get("always_count") is None

# 4. Test context propagation
@pytest.mark.asyncio
async def test_context_propagation() -> None:
    """
    Test that the context is correctly propagated during dispatch.
    """
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

def test_direct_and_decorator_subscription_equivalence() -> None:
    """
    Test that subscribing via the direct method and the decorator both result in handler invocation.
    The results should be unified regardless of subscription method.
    """
    class MyNote(zNote):
        value: int

    called: list = []

    # Direct method subscription (using subscribe global, not as a class method)
    def direct_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        called.append(("direct", note.value, payload.get("extra"), dict(context)))
    subscribe(MyNote)(direct_handler)

    # Decorator subscription
    @subscribe(MyNote)
    def decorator_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        called.append(("decorator", note.value, payload.get("extra"), dict(context)))

    note: MyNote = MyNote(value=42)
    import asyncio
    asyncio.run(note.dispatch(extra="foo"))

    # Both handlers should be called
    assert len(called) == 2
    methods = {c[0] for c in called}
    assert methods == {"direct", "decorator"}
    for method, value, extra, context in called:
        assert value == 42
        assert extra == "foo"
        assert isinstance(context, dict)

def test_hello_world() -> None:
    assert 1 + 1 == 2

def test_polymorphic_subscription_dispatch() -> None:
    """
    Establishes that dispatching a subclass triggers subscriptions to all its ancestors.
    - Subscriptions to zNote, Foo, and Bar are all triggered by Bar dispatch.
    - Subscriptions to Foo and zNote are triggered by Foo dispatch.
    - Subscriptions to zNote are triggered by zNote dispatch.
    """
    from znote import zNote, subscribe
    results = []

    class Foo(zNote):
        foo: int
    class Bar(Foo):
        bar: int

    @subscribe(zNote)
    def handler_znote(note: zNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("zNote", type(note).__name__, dict(payload)))

    @subscribe(Foo)
    def handler_foo(note: Foo, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("Foo", type(note).__name__, dict(payload)))

    @subscribe(Bar)
    def handler_bar(note: Bar, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("Bar", type(note).__name__, dict(payload)))

    import asyncio
    # Dispatch Bar
    bar = Bar(foo=1, bar=2)
    asyncio.run(bar.dispatch(extra="bar"))
    # Dispatch Foo
    foo = Foo(foo=3)
    asyncio.run(foo.dispatch(extra="foo"))
    # Dispatch zNote
    zn = zNote()
    asyncio.run(zn.dispatch(extra="znote"))

    # Bar dispatch triggers all three
    assert ("zNote", "Bar", {"extra": "bar"}) in results
    assert ("Foo", "Bar", {"extra": "bar"}) in results
    assert ("Bar", "Bar", {"extra": "bar"}) in results
    # Foo dispatch triggers Foo and zNote
    assert ("zNote", "Foo", {"extra": "foo"}) in results
    assert ("Foo", "Foo", {"extra": "foo"}) in results
    # zNote dispatch triggers only zNote
    assert ("zNote", "zNote", {"extra": "znote"}) in results
    # No false positives
    assert ("Bar", "Foo", {"extra": "foo"}) not in results
    assert ("Foo", "zNote", {"extra": "znote"}) not in results
    assert ("Bar", "zNote", {"extra": "znote"}) not in results