# JSON Schemas for coach responses
# Note: kept minimal for runtime; for full validation can be loaded into jsonschema.

generic_coach_schema = {
    "$id": "generic_coach_schema",
    "type": "object",
    "properties": {
        "overview": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "priority": {"type": "integer"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["priority", "title", "detail"],
            },
        },
        "drills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "goal": {"type": "string"},
                    "duration_minutes": {"type": "integer"},
                },
                "required": ["name", "goal"],
            },
        },
        "references": {"type": "array", "items": {"type": "string", "format": "uri"}},
        "stream_commentary": {"type": "string"},
    },
    "required": ["overview", "recommendations"],
}

lol_coach_schema = {
    "$id": "lol_coach_schema",
    "allOf": [
        {"$ref": "generic_coach_schema"},
        {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["sr5v5", "aram", "urf", "arena"],
                    "description": "게임 모드 식별자(sr5v5=소환사의 협곡 5v5)",
                },
                "lane": {
                    "type": ["string", "null"],
                    "enum": ["top", "jungle", "mid", "adc", "support", null],
                },
                "champion_tips": {"type": "array", "items": {"type": "string"}},
                "objective_focus": {"type": "string"},
                "item_build": {"type": "array", "items": {"type": "string"}},
                "mode_extras": {
                    "type": "object",
                    "additionalProperties": {"type": ["string", "number", "boolean", "array", "object", "null"]},
                },
            },
            "required": ["mode"],
        },
    ],
}

pubg_coach_schema = {
    "$id": "pubg_coach_schema",
    "allOf": [
        {"$ref": "generic_coach_schema"},
        {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["classic", "tdm", "ranked", "esports"],
                },
                "preferred_map": {
                    "type": "string",
                    "enum": [
                        "Erangel",
                        "Miramar",
                        "Sanhok",
                        "Vikendi",
                        "Taego",
                    ],
                },
                "drop_spots": {"type": "array", "items": {"type": "string"}},
                "weapon_loadout": {"type": "array", "items": {"type": "string"}},
                "rotation_strategy": {"type": "string"},
                "engagement_style": {"type": "string"},
                "mode_extras": {
                    "type": "object",
                    "additionalProperties": {"type": ["string", "number", "boolean", "array", "object", "null"]},
                },
            },
            "required": ["mode", "preferred_map"],
        },
    ],
} 