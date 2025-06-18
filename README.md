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

### Define a Note

```python
from znote import zNote

class MyNote(zNote):
    message: str
```

### Subscribe Handlers

You can subscribe handlers using either the decorator or the direct method:

```python
from znote import subscribe

# Decorator style
@subscribe(MyNote)
def print_handler(note, payload, context):
    print(f"Decorator: {note.message}, payload={payload}, context={context}")

# Direct style
def direct_handler(note, payload, context):
    print(f"Direct: {note.message}, payload={payload}, context={context}")

subscribe(MyNote)(direct_handler)
```

### Filtered Subscriptions

```python
@subscribe(MyNote, lambda note, payload, context: payload.get('important', False))
def important_handler(note, payload, context):
    print("Important note received!")
```

### Dispatching Notes

```python
import asyncio

note = MyNote(message="Hello world")
asyncio.run(note.dispatch(important=True, context={"user": "alice"}))
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
