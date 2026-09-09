from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "dateOperations",
            "def": [{
                "field": Use(str),
                "newFields": [Use(str)],
                "amount": Use(int),
                "dateComponent": Use(str),
                "type": Use(str),
                "pattern": Use(str)
            }]
        }
    ]
})

schema_def = Schema([{
    "field": Use(str),
    "newFields": [Use(str)],
    "amount": Use(int),
    "dateComponent": Use(str),
    "type": Use(str),
    "pattern": Use(str)
}])
