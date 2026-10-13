"""Immutable course records shared by source and packaged catalogs."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    prompt: str
    answer: str
    hint: str
    explanation: str


@dataclass(frozen=True)
class Lesson:
    theory: str
    code: str
    explanation: str
    exercises: tuple[Exercise, ...]
    remember: str = ''
    practice: str = ''
    criteria: str = ''


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    outcome: str
    levels: tuple[str, ...]


