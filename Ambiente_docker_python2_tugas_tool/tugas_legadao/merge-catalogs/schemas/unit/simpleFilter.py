from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "simpleFilter",
            "def": [{
                "fields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "fields": [Use(str)]
}])
