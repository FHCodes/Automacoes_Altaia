from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "transposeCols",
            "def": [{
                "targetFamily": Use(str),
                "colsSet": [{Use(str): Use(str)}],
                Optional("sharedFields"): [Use(str)]
            }]
        }
    ]
})

schema_def = Schema([{
    "targetFamily": Use(str),
    "colsSet": [{Use(str): Use(str)}],
    Optional("sharedFields"): [Use(str)]
}])
