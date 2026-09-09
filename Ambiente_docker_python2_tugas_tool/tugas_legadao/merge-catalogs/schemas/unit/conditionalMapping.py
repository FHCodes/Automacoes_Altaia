from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "conditionalMapping",
            "def": [{
                "condition": Use(str),
                "op": Use(str),
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "condition": Use(str),
    "op": Use(str),
    "newFields": [Use(str)]
}])
