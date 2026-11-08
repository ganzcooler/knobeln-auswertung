"""JSON-Schema für den strukturierten LLM-Output."""

from __future__ import annotations

SCHEMA_NAME = "knobeln_bogen"


def bogen_json_schema() -> dict:
    wurf = {
        "type": "object",
        "additionalProperties": False,
        "required": ["wurf_nr", "roh", "punkte", "hinweis"],
        "properties": {
            "wurf_nr": {"type": "integer", "minimum": 1, "maximum": 12},
            "roh": {"type": "string"},
            "punkte": {"type": ["integer", "null"]},
            "hinweis": {"type": ["string", "null"]},
        },
    }
    summe = {
        "type": "object",
        "additionalProperties": False,
        "required": ["roh", "punkte", "hinweis"],
        "properties": {
            "roh": {"type": "string"},
            "punkte": {"type": ["integer", "null"]},
            "hinweis": {"type": ["string", "null"]},
        },
    }
    spieler = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "position",
            "spieler_nr",
            "spieler_name",
            "wurf_zeilen",
            "summe_bogen",
        ],
        "properties": {
            "position": {"type": "integer", "minimum": 1, "maximum": 4},
            "spieler_nr": {"type": ["string", "null"]},
            "spieler_name": {"type": ["string", "null"]},
            "wurf_zeilen": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": wurf,
            },
            "summe_bogen": summe,
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["bogen_unklar", "hinweis", "durchgang_nr", "spieler"],
        "properties": {
            "bogen_unklar": {"type": "boolean"},
            "hinweis": {"type": ["string", "null"]},
            "durchgang_nr": {"type": ["integer", "null"]},
            "spieler": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": spieler,
            },
        },
    }


def response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": SCHEMA_NAME,
            "strict": True,
            "schema": bogen_json_schema(),
        },
    }
