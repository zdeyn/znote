# znote

> Elegant distributed messaging between Python objects

znote provides a powerful subscribe/emit system with optional filters, enabling decoupled, event-driven design in Python.

## Features

- **Object-to-Object Messaging**: Communicate between Python objects without tight coupling.
- **Filtered Subscriptions**: Handlers can filter on note, payload, and context.
- **Flexible Handlers**: Both sync and async handlers are supported.
- **Unified Context**: Each dispatch can carry a user-supplied context dict, shared by all handlers for that dispatch.

## Installation

```bash
pip install znote
```

## Usage

```python
>>> from znote import zNote, subscribe
>>> class MyNote(zNote):
...     message: str
>>> @subscribe(MyNote)
... def print_handler(note, payload, context):
...     print(f"Decorator: {note.message}, payload={payload}, context={context}")
>>> def direct_handler(note, payload, context):
...     print(f"Direct: {note.message}, payload={payload}, context={context}")
>>> _ = subscribe(MyNote)(direct_handler)
>>> @subscribe(MyNote, lambda note, payload, context: payload.get('important', False))
... def important_handler(note, payload, context):
...     print("Important note received!")
>>> note = MyNote(message="Hello world")
>>> import asyncio
>>> asyncio.run(note.dispatch(important=True, context={"user": "alice"}))
Decorator: Hello world, payload={'important': True}, context={'user': 'alice'}
Direct: Hello world, payload={'important': True}, context={'user': 'alice'}
Important note received!

```

All handlers for `MyNote` will be called if their filter (if any) passes. Each handler receives the note, the payload dict, and the (possibly user-supplied) context dict.

## API

### zNote

- Subclass to define your own message types.
- Use `await note.dispatch(**payload, context=...)` to emit a note.

### subscribe

- Use as a decorator: `@subscribe(MyNote, filter)`
- Or as a function: `subscribe(MyNote, filter)(handler)`
- Handlers receive `(note, payload, context)`

## Limitations

- No dependency injection or handler return value aggregation is implemented (yet).
- Context is per-dispatch and shared by all handlers for that dispatch.
