from schema import Schema, And, Use, Optional, Regex


def validate_int(value):
    return int(value)


schema = Schema({
    "operations": [
        {
            "type": "truncateValue",
            "def": [{
                "startIndex": Use(int),
                "endIndex": Use(int),
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "newFields": [Use(str)],
    "endIndex": Use(int),
    "startIndex": Use(int)
}])
