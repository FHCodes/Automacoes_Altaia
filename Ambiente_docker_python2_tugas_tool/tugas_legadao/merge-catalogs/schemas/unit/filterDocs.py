from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "filterDocs",
            "def": [{
                "by": Use(str),
                "field": Use(str),
                "pattern": Use(str)
            }]
        }
    ]
})

schema_def = Schema([{
    "by": Use(str),
    "field": Use(str),
    "pattern": Use(str)
}])
