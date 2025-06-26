import pytest
from typing import Any, Dict
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

def test_hello_world() -> None:
    """Simple hello world test."""
    assert 1 + 1 == 2

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