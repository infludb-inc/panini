OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "author_id": {"type": "string"},
        "external_id": {"type": "string"},
        "is_liked_by_creator": {"type": "boolean"},
        "is_top_lvl": {"type": "boolean"},
        "likecount": {"type": "integer"},
        "published_date": {"type": "string"},
        "text": {"type": "string"},
    },
    "required": ["external_id"]
}
