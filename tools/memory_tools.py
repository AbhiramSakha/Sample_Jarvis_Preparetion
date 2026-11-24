from core.memory import memory
from tools.registry import registry


@registry.register(
    "remember",
    "Save a lasting fact about the user (name, preferences, routines) for future conversations.",
    {
        "key": {"type": "string", "description": "Short label, e.g. 'favorite_music'"},
        "value": {"type": "string", "description": "The fact"},
    },
    ["key", "value"],
)
def remember(key: str, value: str):
    memory.remember(key, value)
    return f"Saved: {key} = {value}"


@registry.register(
    "take_note",
    "Save a note or reminder text for the user.",
    {"text": {"type": "string"}},
    ["text"],
)
def take_note(text: str):
    return f"Note #{memory.add_note(text)} saved."


@registry.register("list_notes", "List the user's most recent notes.")
def list_notes():
    notes = memory.list_notes()
    return "\n".join(f"#{i} [{c}] {t}" for i, t, c in notes) or "No notes yet."



@registry.register(
    "delete_note",
    "Delete a note by its id.",
    {"note_id": {"type": "integer"}},
    ["note_id"],
    confirm=True,  # destructive, so ask first
)
def delete_note(note_id: int):
    return "Deleted." if memory.delete_note(note_id) else "No such note."