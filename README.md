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
...     return f"Decorator: {note.message}, payload={payload}, context={context}"
>>> def direct_handler(note, payload, context):
...     return f"Direct: {note.message}, payload={payload}, context={context}"
>>> _ = subscribe(MyNote)(direct_handler)
>>> @subscribe(MyNote, lambda note, payload, context: payload.get('important', False))
... def important_handler(note, payload, context):
...     return "Important note received!"
>>> note = MyNote(message="Hello world")
>>> import asyncio
>>> emission = asyncio.run(note.emit(important=True, context={"user": "alice"}))
>>> for response in emission:
...     print(response.result)
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

## Subscribing to Ancestor Classes

You can subscribe to a base note class and receive all notes of its subclasses:

```python
>>> from znote import zNote, subscribe
>>> class BaseNote(zNote):
...     pass
>>> class ChildNote(BaseNote):
...     pass
>>> @subscribe(BaseNote)
... def base_handler(note, payload, context):
...     return f"Base handler: {type(note).__name__}, payload={payload}"
>>> note = ChildNote()
>>> import asyncio
>>> emission = asyncio.run(note.emit(x=1))
>>> for response in emission:
...     print(response.result)
Base handler: ChildNote, payload={'x': 1}

```

## Limitations

- No dependency injection or handler return value aggregation is implemented (yet).
- Context is per-dispatch and shared by all handlers for that dispatch.
