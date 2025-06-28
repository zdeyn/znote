# znote

> Elegant distributed messaging between Python objects

znote provides a powerful subscribe/emit system with optional filters, enabling decoupled, event-driven design in Python.

## Features

- **Object-to-Object Messaging**: Communicate between Python objects without tight coupling.
- **Filtered Subscriptions**: Handlers can filter on note, payload, and context.
- **Flexible Handlers**: Both sync and async handlers are supported.
- **Unified Context**: Each dispatch can carry a user-supplied context dict, shared by all handlers for that dispatch.
- **Deduplication**: Handlers subscribed to both a parent and child note type are only called once per emission.
- **Introspectable Emissions**: Emission and Response objects have clear, informative `__repr__` and `__str__` for debugging and interactive use.

## Installation

```bash
pip install znote
```

## Usage

```python
>>> from znote import zNote, subscribe
>>> import asyncio
>>> class MyNote(zNote):
...     message: str
>>> @subscribe(MyNote)
... def everything_handler(note):
...     return f"E: {note.message}"
>>> @subscribe(MyNote, lambda n: 'important' in n.message.lower())
... def important_handler(note):
...     return f"I: {note.message}"
>>> note_a = MyNote(message="Hello, World!")
>>> emission_a = asyncio.run(note_a.emit())
>>> for response in emission_a:
...     print(response)
Response from everything_handler on MyNote(message='Hello, World!'): 'E: Hello, World!'
>>> note_b = MyNote(message="Important Message!")
>>> emission_b = asyncio.run(note_b.emit())
>>> for response in emission_b:
...     print(response)
Response from everything_handler on MyNote(message='Important Message!'): 'E: Important Message!'
Response from important_handler on MyNote(message='Important Message!'): 'I: Important Message!'

```

All handlers for `MyNote` will be called if their filter (if any) passes. Each handler receives the note instance. You may also define handlers that accept `(note, payload)` or `(note, payload, context)` if you need those values.

**Real-world usage tip:**
- The `payload` is for the *attachments/entities that go with the note* (e.g. user, files, metadata, etc).
- The `context` is for *internal storage for parallel processing, scratch-space, or handler coordination* (e.g. tracking which handlers ran, accumulating results, or sharing state between handlers during a single emission).
- For example, you might pass the user as part of the payload, and use the context to track if a note is 'important' or to accumulate logs during emission.

## API

### zNote

- Subclass to define your own message types.
- Use `await note.emit(**payload, context=...)` to emit a note. Returns an `Emission` object for introspection.
- `repr(note)` and `str(note)` show all fields, e.g. `MyNote(message='hi', count=2)`.

### subscribe

- Use as a decorator: `@subscribe(MyNote, filter)`
- Or as a function: `subscribe(MyNote, filter)(handler)`
- Handlers receive `(note, payload, context)`

### Emission and Response

- `Emission` is iterable and contains a `_Response` for each handler call.
- `repr(emission)` and `str(emission)` show all handler results and note details.
- `repr(response)` and `str(response)` show the handler, note, and result.

## Subscribing to Ancestor Classes

You can subscribe to a base note class and receive all notes of its subclasses. Handlers are deduplicated per emission:

```python
>>> from znote import zNote, subscribe
>>> class BaseNote(zNote):
...     pass
>>> class ChildNote(BaseNote):
...     pass
>>> @subscribe(BaseNote)
... def base_handler(note, payload, context):
...     return f"Base handler: {repr(note)}, payload={payload}"
>>> note = ChildNote()
>>> import asyncio
>>> emission = asyncio.run(note.emit(x=1))
>>> for response in emission:
...     print(response)
Response from base_handler on ChildNote(): "Base handler: ChildNote(), payload={'x': 1}"

```

## Comments

- No dependency injection is implemented (yet).
- Context is per-dispatch and shared by all handlers for that dispatch.
