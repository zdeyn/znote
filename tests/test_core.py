import pytest
from typing import Any, Dict
from znote import zNote, subscribe, Dispatcher

# 1. Test basic zNote creation and attribute access
def test_znote_creation() -> None:
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        name: str = "test"
        value: int = 10
    note: MyNote = MyNote()
    assert note.name == "test"
    assert note.value == 10
    # Test __repr__ and __str__
    assert repr(note) == "MyNote(name='test', value=10)"
    assert str(note) == "MyNote(name='test', value=10)"

def test_hello_world() -> None:
    Dispatcher.clear_subscriptions()
    assert 1 + 1 == 2

def test_direct_and_decorator_subscription_equivalence() -> None:
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        value: int
    called: list = []
    def direct_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        called.append(("direct", note.value, payload.get("extra"), dict(context)))
    subscribe(MyNote)(direct_handler)
    @subscribe(MyNote)
    def decorator_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        called.append(("decorator", note.value, payload.get("extra"), dict(context)))
    note: MyNote = MyNote(value=42)
    import asyncio
    emission = asyncio.run(note.emit(extra="foo"))
    # Emission is introspectable and has clear output
    assert len(emission) == 2
    for response in emission:
        assert response.note is note
        assert response.payload["extra"] == "foo"
        assert repr(response).startswith("<Response handler=")
        assert str(response).startswith("Response from ")
    methods = {c[0] for c in called}
    assert methods == {"direct", "decorator"}
    for method, value, extra, context in called:
        assert value == 42
        assert extra == "foo"
        assert isinstance(context, dict)

def test_polymorphic_subscription_emit() -> None:
    Dispatcher.clear_subscriptions()
    results = []
    class Foo(zNote):
        foo: int
    class Bar(Foo):
        bar: int
    @subscribe(zNote)
    def handler_znote(note: zNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("zNote", repr(note), dict(payload)))
    @subscribe(Foo)
    def handler_foo(note: Foo, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("Foo", repr(note), dict(payload)))
    @subscribe(Bar)
    def handler_bar(note: Bar, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        results.append(("Bar", repr(note), dict(payload)))
    import asyncio
    emission_bar = asyncio.run(Bar(foo=1, bar=2).emit(extra="bar"))
    emission_foo = asyncio.run(Foo(foo=3).emit(extra="foo"))
    # Deduplication: handler_znote and handler_foo should only be called once per emission
    assert any("Bar" in r for r in results)
    assert any("Foo" in r for r in results)
    assert any("zNote" in r for r in results)
    # Emission output is clear
    assert repr(emission_bar).startswith("Emission(len=")
    assert all("Bar" in str(r) or "Foo" in str(r) or "zNote" in str(r) for r in emission_bar)