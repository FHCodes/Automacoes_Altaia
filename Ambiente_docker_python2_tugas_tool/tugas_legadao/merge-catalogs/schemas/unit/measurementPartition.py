from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "measurementPartition",
            "def": [{
                "measurements": [Use(str)],
                Optional("sharedFields"): [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "measurements": [Use(str)],
    Optional("sharedFields"): [Use(str)]
}])
