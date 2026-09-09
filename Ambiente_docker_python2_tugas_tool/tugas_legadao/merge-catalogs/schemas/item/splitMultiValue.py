from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "splitMultiValue",
            "def": [{
                "compressed": Use(str),
                "delimiter": Use(str),
                "newFields": [Use(str)],
                Optional("allowMismatchFields"): Use(bool)
            }]
        }
    ]
})

schema_def = Schema([{

    "compressed": Use(str),
    "delimiter": Use(str),
    "newFields": [Use(str)],
    Optional("allowMismatchFields"): Use(bool)
}])
