from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "csvLineIntoKnownValues",
            "def": [{
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "newFields": [Use(str)]
}])
