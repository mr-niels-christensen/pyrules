import unittest
from pyrules2 import when, rule, RuleBook, person, no
from pyrules2.wolframalpha import wap
import urllib


class Test(unittest.TestCase):
    def test_foo(self):
        server = 'http://api.wolframalpha.com/v2/query'
        appid = 'JUTQGW-TGXG9E75E4'
        input = 'driving time from Peterhead to Aboyne'

        waeo = wap.WolframAlphaEngine(appid, server)
        query = waeo.CreateQuery(input)
        result = waeo.PerformQuery(query)
        waeqr = wap.WolframAlphaQueryResult(result)
        jsonresult = waeqr.JsonResult()
        from pprint import pprint
        from json import loads
        pprint(loads(jsonresult))


if __name__ == "__main__":
    unittest.main()
