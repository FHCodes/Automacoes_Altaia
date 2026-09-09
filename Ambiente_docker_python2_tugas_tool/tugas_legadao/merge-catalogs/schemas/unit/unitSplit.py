from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "unitSplit",
            "def": [{
                "id": Use(str),
                "regexes": [{
                    "newUnit": Use(str),
                    "pattern": Use(str)
                }]
            }]
        }
    ]
})

schema_def = Schema([{
    "id": Use(str),
    "regexes": [{
        "newUnit": Use(str),
        "pattern": Use(str)
    }]
}])
