from schema import Schema, And, Or, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "dictionaryReplace",
            "def": [{
                "items": [{"key": Or(Use(str),None), "value": Use(str)}]
            }]
        }
    ]
})

schema_def = Schema([{
    "items": [{"key": Or(Use(str),None), "value": Use(str)}]
}])
