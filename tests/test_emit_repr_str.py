from znote import zNote, subscribe, Emission, Dispatcher
import asyncio

def test_repr_str_note_emission_response():
    Dispatcher.clear_subscriptions()
    class MyNote(zNote):
        foo: int
        bar: str
    @subscribe(MyNote)
    def handler(note, payload, context):
        # payload is for attachments/entities (e.g. user, files)
        # context is for internal scratch-space, etc
        return f"handled {note.foo} {note.bar}, user={payload.get('user')}, flag={context.get('flag')}"
    note = MyNote(foo=42, bar="baz")
    emission = asyncio.run(note.emit(user='bob', context={'flag': True}))
    # Test zNote __repr__ and __str__
    note_repr = repr(note)
    note_str = str(note)
    assert note_repr.startswith("MyNote(") and "foo=42" in note_repr and "bar='baz'" in note_repr
    assert note_str == note_repr
    # Test Emission __repr__ and __str__
    emission_repr = repr(emission)
    emission_str = str(emission)
    assert emission_repr.startswith("Emission(len=1")
    assert "handled 42 baz" in emission_repr
    assert "user=bob" in emission_repr
    assert "flag=True" in emission_repr
    # Now expect the new format with note details in the string
    assert "Response from `handler` to MyNote(foo=42, bar='baz'): 'handled 42 baz, user=bob, flag=True'" in emission_str
    # Test Response __repr__ and __str__
    response = emission[0]
    response_repr = repr(response)
    response_str = str(response)
    assert response_repr.startswith("<Response handler=handler note=MyNote(foo=42, bar='baz') result='handled 42 baz, user=bob, flag=True'")
    assert response_str == "Response from `handler` to MyNote(foo=42, bar='baz'): 'handled 42 baz, user=bob, flag=True'"
    # Print for visual inspection
    print("NOTE __repr__:", note_repr)
    print("EMISSION __repr__:", emission_repr)
    print("RESPONSE __repr__:", response_repr)
    print("EMISSION __str__:\n", emission_str)
    print("RESPONSE __str__:", response_str)
    # In test_emit_repr_str.py, update expected string for __str__
    # Example: 'Response from print_handler on MyNote(message=...)' -> 'Response from `print_handler` to MyNote(message=...)'
