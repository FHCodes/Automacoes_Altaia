from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "concatFields",
            "def": [{
                Optional("finalString"): Use(str),
                Optional("pattern"): Use(str),
                "stringFromFields": Use(str),
                "fields": [Use(str)],
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    Optional("finalString"): Use(str),
    Optional("pattern"): Use(str),
    "stringFromFields": Use(str),
    "fields": [Use(str)],
    "newFields": [Use(str)]
}])
