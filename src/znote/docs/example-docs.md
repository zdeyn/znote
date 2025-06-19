# zNote: Elegant Distributed Messaging for Python

Tired of tangled dependencies and complex event handling? Meet `zNote`, a lightweight Python library designed to simplify communication between objects using a publish/subscribe pattern. Even in its early stages, `zNote` offers a powerful and flexible way to build decoupled, event-driven applications.

## What is zNote?

`zNote` allows you to define message types (called "notes") and subscribe handlers to those notes. When a note is "dispatched," all subscribed handlers receive it, along with any relevant data (the "payload") and a shared context. This approach promotes loose coupling, making your code more modular, testable, and maintainable.

## Simplicity in Action

Let's start with a basic example to illustrate the core concepts:

```python
from znote import zNote, subscribe
import asyncio

# 1. Define a Note
class MyNote(zNote):
    message: str

# 2. Subscribe a Handler
@subscribe(MyNote)
async def my_handler(note: MyNote, payload: dict, context: dict):
    print(f"Received note: {note.message}")
    if payload:
        print(f"Payload: {payload}")
    if context:
        print(f"Context: {context}")

# 3. Create and Dispatch a Note
async def main():
    note = MyNote(message="Hello, zNote!")
    await note.dispatch(extra_data="This is the payload", context={"user": "Alice"})

asyncio.run(main())
```

In this example:

1.  We define a `MyNote` class, inheriting from `zNote`, with a `message` attribute.
2.  We use the `@subscribe` decorator to register `my_handler` to receive `MyNote` instances.
3.  We create an instance of `MyNote` and dispatch it using `note.dispatch()`, including a payload and context.

When you run this code, you'll see the handler print the message from the note, along with the payload and context.

## Power and Flexibility

`zNote` provides more than just basic message passing. Here are some key features that highlight its power and flexibility:

### Filters

You can add filters to your subscriptions to selectively handle notes based on their content, the payload, or the context:

```python
from znote import zNote, subscribe
import asyncio

class StatusUpdate(zNote):
    status: str

@subscribe(StatusUpdate, lambda note, payload, context: note.status == "error")
async def error_handler(note: StatusUpdate, payload: dict, context: dict):
    print(f"Error status: {note.status}")

async def main():
    await StatusUpdate(status="ok").dispatch()  # No output
    await StatusUpdate(status="error").dispatch()  # Prints "Error status: error"

asyncio.run(main())
```

### Context

The `context` is a dictionary that's passed to all handlers during a dispatch. This allows you to share information between handlers, such as user authentication details, request IDs, or any other relevant data.  The context is mutable, and changes made by one handler are visible to subsequent handlers in the same dispatch.

### Asynchronous Support

`zNote` seamlessly supports both synchronous and asynchronous handlers, making it suitable for a wide range of applications.

### Inheritance

Subscriptions work with inheritance.  If you subscribe to a parent class, the handler will be triggered for instances of any subclass:

```python
from znote import zNote, subscribe
import asyncio

class BaseNote(zNote):
    pass

class DerivedNote(BaseNote):
    message: str

@subscribe(BaseNote)
async def base_handler(note: BaseNote, payload: dict, context: dict):
    print("Base handler called!")

async def main():
    await DerivedNote(message="Hello").dispatch() # Triggers base_handler

asyncio.run(main())
```

## Early Days, Big Potential

`zNote` is still under active development, but it's already a valuable tool for building decoupled and event-driven Python applications. Future development will focus on features like:

*   Dependency injection for handlers
*   Handler return value aggregation
*   More sophisticated filtering options

## Get Involved

Try out `zNote` and let us know what you think! You can install it via pip:

```bash
pip install znote
```

Check out the [README](link to your README) for more detailed information and examples. We welcome