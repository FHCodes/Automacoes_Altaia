from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "fixedValue",
            "def": [{
                "newFields": [{"field": Use(str), "value": Use(str)}]
            }]
        }
    ]
})

schema_def = Schema([{
    "newFields": [{"field": Use(str), "value": Use(str)}]
}])
