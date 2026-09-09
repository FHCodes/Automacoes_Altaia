from schema import Schema, And, Use, Optional, Regex, Or

schema = Schema({
    "operations": [
        {
            "type": "epochToTimestamp",
            "def": [{Optional("inputTimeUnit"): Or("days", "hours", "minutes", "seconds", "milliseconds", "microseconds", "nanoseconds")}]
        }
    ]
})

schema_def = Schema([{Optional("inputTimeUnit"): Or("days", "hours", "minutes", "seconds", "milliseconds", "microseconds", "nanoseconds")}])