import pytest
from typing import Any, Dict
from znote import zNote, subscribe

# 1. Test basic zNote creation and attribute access
def test_znote_creation() -> None:
    class MyNote(zNote):
        name: str = "test"
        value: int = 10
    note: MyNote = MyNote()
    assert note.name == "test"
    assert note.value == 10

def test_hello_world() -> None:
    assert 1 + 1 == 2

def test_direct_and_decorator_subscription_equivalence() -> None:
    class MyNote(zNote):
        value: int
    called: list = []
    def direct_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        called.append(("direct", note.value, payload.get("extra"), dict(context)))
    subscribe(MyNote)(direct_handler)
    @subscribe(MyNote)
    def decorator_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        called.append(("decorator", note.value, payload.get("extra"), dict(context)))
    note: MyNote = MyNote(value=42)
    import asyncio
    emission = asyncio.run(note.emit(extra="foo"))
    # Using Emission is optional, but we can introspect if we want:
    assert len(emission) == 2
    for response in emission:
        assert response.note is note
        assert response.payload["extra"] == "foo"
    methods = {c[0] for c in called}
    assert methods == {"direct", "decorator"}
    for method, value, extra, context in called:
        assert value == 42
        assert extra == "foo"
        assert isinstance(context, dict)

def test_polymorphic_subscription_emit() -> None:
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
    emission_bar = asyncio.run(Bar(foo=1, bar=2).emit(extra="bar"))
    emission_foo = asyncio.run(Foo(foo=3).emit(extra="foo"))
    emission_zn = asyncio.run(zNote().emit(extra="znote"))
    # Optionally introspect Emission objects:
    assert any(r.note.__class__.__name__ == "Bar" for r in emission_bar)
    assert ("zNote", "Bar", {"extra": "bar"}) in results
    assert ("Foo", "Bar", {"extra": "bar"}) in results
    assert ("Bar", "Bar", {"extra": "bar"}) in results
    assert ("zNote", "Foo", {"extra": "foo"}) in results
    assert ("Foo", "Foo", {"extra": "foo"}) in results
    assert ("zNote", "zNote", {"extra": "znote"}) in results
    assert ("Bar", "Foo", {"extra": "foo"}) not in results
    assert ("Foo", "zNote", {"extra": "znote"}) not in results
    assert ("Bar", "zNote", {"extra": "znote"}) not in results