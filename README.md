# znote

> Distributed messaging between Python objects made elegant

znote provides a powerful subscribe/emit system with filtered callbacks, enabling a unique approach to domain-driven design in Python applications.

## Features

- **Object-to-Object Messaging**: Communication between Python objects without tight coupling
- **Filtered Subscriptions**: Target specific message types with powerful filtering capabilities
- **Callback System**: Define responsive behaviors triggered by specific events
- **Domain-Driven Design**: Facilitate clean separation of concerns in complex applications

## Installation

```bash
pip install znote
```

## Why znote?

znote allows Python developers to implement sophisticated messaging patterns while maintaining clean, decoupled code. Whether you're building a complex application architecture or simply need components to communicate effectively, znote provides the tools to make it happen.


## Mental model

`zNote` is our root message class, based on a `pydantic` `BaseModel`

Inherit from it as you wish:

```python
from znote import zNote
from znote import before, on, after, replace, augment, observe

def GreetSomeone(zNote):
    name : str

def HelloAnonymous(GreetSomeone):
    name : Literal["World!"]

def HelloSomeone(GreetSomeone):
    name : str

def HelloAdmin(HelloSomeone):
    role : str



class Logger:

    @on(zNote)
    def an_observer(self, note : zNote):
        print(f"{self.__name__}: ({note.id}) I saw {note.payload} from {note.src}, addressed to {note.dest or 'Everyone'})")
        print(f"{self.__name__}: ({note.id}) History:")
        for h in note.history:
            print(f"  {h.seen_at} -> {h.seen_by}: {h.log}")
    
class Foo:

    def greeter(self, name : Optional[str] = None) -> str:

        # emit a GreetSomeone, include name in payload
        return f"Hello, {await GreetSomeone(name = name).emit()}!"

class Bar:

    @replace(GreetSomeone, lambda n: n is None)
    def of_course_its_world(self, note : GreetSomeone) -> HelloAnonymous | None:
        return HelloAnonymous(replace=note, name='world')

    @replace(GreetSomeone, lambda n: n != 'zdeyn')
    def wave_to_the_plebians(self, note : GreetSomeone) -> HelloSomeone | None:
        return HelloSomeone(replace=note, name=name)

    @replace(GreetSomeone, lambda n: n == 'zdeyn')
    def oh_hai_zdeyn(self, note : GreetSomeone) -> HelloAdmin | None:
        return HelloAdmin(replace=note, name=name, role='admin')

```