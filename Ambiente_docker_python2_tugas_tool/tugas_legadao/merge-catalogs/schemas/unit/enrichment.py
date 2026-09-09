from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "enrichment",
            "def": [{
                "enrichmentId": Use(str),
                "datasourceId": Use(str),
                "scope": Use(str),
                "corrKeys": [Use(str)],
                "newFields": [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "enrichmentId": Use(str),
    "datasourceId": Use(str),
    "scope": Use(str),
    "corrKeys": [Use(str)],
    "newFields": [Use(str)]
}])
