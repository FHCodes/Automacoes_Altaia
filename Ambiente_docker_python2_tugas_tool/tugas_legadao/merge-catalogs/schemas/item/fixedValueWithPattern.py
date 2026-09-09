from schema import Schema, Use

schema = Schema({
    "operations": [
        {
            "type": "fixedValueWithPattern",
            "def": [{
                "pattern": Use(str),
                "newFields": [{"field": Use(str), "value": Use(str)}]
            }]
        }
    ]
})

schema_def = Schema([{
    "pattern": Use(str),
    "newFields": [{"field": Use(str), "value": Use(str)}]
}])
