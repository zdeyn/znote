from znote import zNote, subscribe
from znote import Dispatcher
from typing import Dict, Any

def test_simple_subscription_emit():
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        greeting: str
    called = []
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        context["modified"] = True
        called.append((note, payload, context))
    import asyncio
    emission = asyncio.run(MyNote(greeting="hello").emit(foo={"test-key": "test-value"}))
    assert any(response.note.greeting == "hello" and response.payload["foo"] == {"test-key": "test-value"} and response.context["modified"] is True for response in emission)
    assert any(c[0].greeting == "hello" for c in called)
    # Emission output is clear
    assert repr(emission).startswith("Emission(len=")
    assert all("MyNote" in str(r) for r in emission)

def test_filtered_subscription_emit():
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        id: int
    called = []
    @subscribe(MyNote)
    async def always(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        context["always_count"] = context.get("always_count", 0) + 1
        called.append(("always", note.id, payload["count"], dict(context)))
    @subscribe(MyNote, lambda note, payload, context: payload["count"] == 2)
    async def filtered(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
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
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        data: str
    initial_context: Dict[str, Any] = {"user_id": "test_user"}
    called = []
    @subscribe(MyNote)
    async def my_handler(note: MyNote, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        called.append(context)
    import asyncio
    emission = asyncio.run(MyNote(data="hello").emit(context=initial_context))
    assert any(c == initial_context for c in called)
    assert any(response.context == initial_context for response in emission)
    # Emission output is clear
    assert repr(emission).startswith("Emission(len=")
    assert all("MyNote" in str(r) for r in emission)

def test_no_duplicate_handler_invocation():
    Dispatcher.clear_subscriptions()
    class ParentNote(zNote):
        pass
    class ChildNote(ParentNote):
        pass
    called = []
    def handler(note, payload, context):
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        called.append(note)
    subscribe(ParentNote)(handler)
    subscribe(ChildNote)(handler)
    import asyncio
    emission = asyncio.run(ChildNote().emit())
    # Handler should only be called once, with the ChildNote instance
    assert len(called) == 1
    assert isinstance(called[0], ChildNote)
    assert all(isinstance(r.note, ChildNote) for r in emission)
    # Emission output is clear
    assert repr(emission).startswith("Emission(len=1")
    assert all("ChildNote" in str(r) for r in emission)
