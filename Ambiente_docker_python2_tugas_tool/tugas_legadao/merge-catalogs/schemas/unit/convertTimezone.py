from schema import Schema, And, Use, Optional, Regex

schema = Schema({
    "operations": [
        {
            "type": "convertTimezone",
            "def": [{
                "field": Use(str),
                "newFields": [Use(str)],
                "inTimezone": Use(str),
                "inPattern": Use(str),
                "outTimezone": Use(str),
                "outPattern": Use(str)
            }]
        }
    ]
})

schema_def = Schema([{
    "field": Use(str),
    "newFields": [Use(str)],
    "inTimezone": Use(str),
    "inPattern": Use(str),
    "outTimezone": Use(str),
    "outPattern": Use(str)

}])
