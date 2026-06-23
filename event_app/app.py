#!/usr/bin/env python3
"""Event Registration & Check-in Demo — Core Logic + Unittest.

Pure Python standard library only. No Flask, FastAPI, pandas, numpy.
"""

import json
import os
import tempfile
import unittest
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """A single event with registration and check-in."""
    id: str
    title: str
    capacity: int
    registrations: dict = field(default_factory=dict)  # email -> name
    checked_in: set = field(default_factory=set)        # set of email

    def remaining_spots(self) -> int:
        return self.capacity - len(self.registrations)

    def register(self, email: str, name: str) -> str:
        """Register a person. Returns status message."""
        email = email.strip().lower()
        if not email or "@" not in email:
            return "ERROR: Invalid email address."
        if email in self.registrations:
            return "ERROR: Already registered."
        if len(self.registrations) >= self.capacity:
            return "ERROR: Event is full."
        self.registrations[email] = name.strip()
        return f"OK: {name} registered for '{self.title}'."

    def check_in(self, email: str) -> str:
        """Check in a registered person. Returns status message."""
        email = email.strip().lower()
        if email not in self.registrations:
            return "ERROR: Not registered."
        if email in self.checked_in:
            return "ERROR: Already checked in."
        self.checked_in.add(email)
        return f"OK: {self.registrations[email]} checked in."

    def stats(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "capacity": self.capacity,
            "registered": len(self.registrations),
            "checked_in": len(self.checked_in),
            "remaining": self.remaining_spots(),
        }


class EventStore:
    """In-memory store for events. Could be swapped for a DB later."""

    def __init__(self):
        self._events: dict[str, Event] = {}

    def add(self, event: Event) -> None:
        self._events[event.id] = event

    def get(self, event_id: str) -> Optional[Event]:
        return self._events.get(event_id)

    def list_events(self) -> list[dict]:
        return [e.stats() for e in self._events.values()]

    def save_to_file(self, path: str) -> None:
        data = {eid: asdict(e) for eid, e in self._events.items()}
        for eid, d in data.items():
            d["checked_in"] = list(d["checked_in"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, d in data.items():
            d["checked_in"] = set(d["checked_in"])
            self._events[eid] = Event(**d)


def demo():
    """Run a quick demo scenario."""
    store = EventStore()
    store.add(Event(id="e1", title="Python Workshop", capacity=3))
    store.add(Event(id="e2", title="AI Meetup", capacity=5))
    e = store.get("e1")
    print(e.register("alice@example.com", "Alice"))
    print(e.register("bob@example.com", "Bob"))
    print(e.register("carol@example.com", "Carol"))
    print(e.register("dave@example.com", "Dave"))
    print(e.check_in("alice@example.com"))
    print(e.check_in("bob@example.com"))
    print(e.check_in("alice@example.com"))
    print(e.check_in("unknown@example.com"))
    print("\nStats:", json.dumps(e.stats(), indent=2))
    print("\nAll events:", json.dumps(store.list_events(), indent=2))


class TestEvent(unittest.TestCase):
    def setUp(self):
        self.event = Event(id="t1", title="Test Event", capacity=2)

    def test_register_success(self):
        msg = self.event.register("a@b.com", "Alice")
        self.assertIn("OK", msg)
        self.assertIn("a@b.com", self.event.registrations)

    def test_register_invalid_email(self):
        msg = self.event.register("notanemail", "No")
        self.assertIn("ERROR", msg)

    def test_register_duplicate(self):
        self.event.register("a@b.com", "Alice")
        msg = self.event.register("a@b.com", "Alice Again")
        self.assertIn("ERROR", msg)

    def test_register_full(self):
        self.event.register("a@b.com", "A")
        self.event.register("b@c.com", "B")
        msg = self.event.register("c@d.com", "C")
        self.assertIn("ERROR", msg)
        self.assertIn("full", msg.lower())

    def test_check_in_success(self):
        self.event.register("a@b.com", "Alice")
        msg = self.event.check_in("a@b.com")
        self.assertIn("OK", msg)
        self.assertIn("a@b.com", self.event.checked_in)

    def test_check_in_not_registered(self):
        msg = self.event.check_in("x@y.com")
        self.assertIn("ERROR", msg)

    def test_check_in_duplicate(self):
        self.event.register("a@b.com", "Alice")
        self.event.check_in("a@b.com")
        msg = self.event.check_in("a@b.com")
        self.assertIn("ERROR", msg)

    def test_remaining_spots(self):
        self.assertEqual(self.event.remaining_spots(), 2)
        self.event.register("a@b.com", "A")
        self.assertEqual(self.event.remaining_spots(), 1)

    def test_stats(self):
        self.event.register("a@b.com", "Alice")
        self.event.check_in("a@b.com")
        s = self.event.stats()
        self.assertEqual(s["registered"], 1)
        self.assertEqual(s["checked_in"], 1)
        self.assertEqual(s["remaining"], 1)


class TestEventStore(unittest.TestCase):
    def setUp(self):
        self.store = EventStore()
        self.store.add(Event(id="e1", title="Workshop", capacity=10))

    def test_get_event(self):
        e = self.store.get("e1")
        self.assertIsNotNone(e)
        self.assertEqual(e.title, "Workshop")

    def test_get_missing(self):
        self.assertIsNone(self.store.get("nope"))

    def test_list_events(self):
        events = self.store.list_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Workshop")

    def test_save_and_load(self):
        e = self.store.get("e1")
        e.register("alice@example.com", "Alice")
        e.check_in("alice@example.com")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.store.save_to_file(path)
            new_store = EventStore()
            new_store.load_from_file(path)
            loaded = new_store.get("e1")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.title, "Workshop")
            self.assertIn("alice@example.com", loaded.registrations)
            self.assertIn("alice@example.com", loaded.checked_in)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    print("=" * 50)
    print("Event App Demo")
    print("=" * 50)
    demo()
    print("\n" + "=" * 50)
    print("Running unit tests...")
    print("=" * 50)
    unittest.main(verbosity=2)
