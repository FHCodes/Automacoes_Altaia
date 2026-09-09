from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "timestampToEpoch",
            "def": []
        }
    ]
})

schema_def = Schema([])
