from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "applyRegex",
            "def": [{
                "pattern": Use(str),
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "pattern": Use(str),
    "newFields": [Use(str)]
}])
