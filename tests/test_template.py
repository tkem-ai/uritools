import unittest

from uritools import uritemplate

# RFC 6570 3.2: example variables
RFC6570_VARIABLES = {
    "count": ["one", "two", "three"],
    "dom": ["example", "com"],
    "dub": "me/too",
    "hello": "Hello World!",
    "half": "50%",
    "var": "value",
    "who": "fred",
    "base": "http://example.com/home/",
    "path": "/foo/bar",
    "list": ["red", "green", "blue"],
    "keys": {"semi": ";", "dot": ".", "comma": ","},
    "v": "6",
    "x": "1024",
    "y": "768",
    "empty": "",
    "empty_keys": {},
    "undef": None,
}


class TemplateTest(unittest.TestCase):
    def check(self, template, expected, variables):
        for tmpl in (template, template.encode("utf-8")):
            result = uritemplate(tmpl).expand(variables)
            msg = "%r -> %r (variables=%r)" % (tmpl, result, variables)
            if isinstance(expected, list):
                self.assertIn(result, expected, msg)
            else:
                self.assertEqual(expected, result, msg)

    def test_rfc6570_s2_1_literals(self):
        """uritemplate test cases from RFC 6570 2.1 Literals"""
        variables = {"count": ["one", "two", "three"]}
        cases = [
            ("'{count}'", "'one,two,three'"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_1_variable_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.1 Variable Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{count}", "one,two,three"),
            ("{count*}", "one,two,three"),
            ("{/count}", "/one,two,three"),
            ("{/count*}", "/one/two/three"),
            ("{;count}", ";count=one,two,three"),
            ("{;count*}", ";count=one;count=two;count=three"),
            ("{?count}", "?count=one,two,three"),
            ("{?count*}", "?count=one&count=two&count=three"),
            ("{&count*}", "&count=one&count=two&count=three"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_2_simple_string_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.2 Simple String Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{var}", "value"),
            ("{hello}", "Hello%20World%21"),
            ("{half}", "50%25"),
            ("O{empty}X", "OX"),
            ("O{undef}X", "OX"),
            ("{x,y}", "1024,768"),
            ("{x,hello,y}", "1024,Hello%20World%21,768"),
            ("?{x,empty}", "?1024,"),
            ("?{x,undef}", "?1024"),
            ("?{undef,y}", "?768"),
            ("{var:3}", "val"),
            ("{var:30}", "value"),
            ("{list}", "red,green,blue"),
            ("{list*}", "red,green,blue"),
            (
                "{keys}",
                [
                    "comma,%2C,dot,.,semi,%3B",
                    "comma,%2C,semi,%3B,dot,.",
                    "dot,.,comma,%2C,semi,%3B",
                    "dot,.,semi,%3B,comma,%2C",
                    "semi,%3B,comma,%2C,dot,.",
                    "semi,%3B,dot,.,comma,%2C",
                ],
            ),
            (
                "{keys*}",
                [
                    "comma=%2C,dot=.,semi=%3B",
                    "comma=%2C,semi=%3B,dot=.",
                    "dot=.,comma=%2C,semi=%3B",
                    "dot=.,semi=%3B,comma=%2C",
                    "semi=%3B,comma=%2C,dot=.",
                    "semi=%3B,dot=.,comma=%2C",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_3_reserved_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.3 Reserved Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{+var}", "value"),
            ("{/var,empty}", "/value/"),
            ("{/var,undef}", "/value"),
            ("{+hello}", "Hello%20World!"),
            ("{+half}", "50%25"),
            ("{base}index", "http%3A%2F%2Fexample.com%2Fhome%2Findex"),
            ("{+base}index", "http://example.com/home/index"),
            ("O{+empty}X", "OX"),
            ("O{+undef}X", "OX"),
            ("{+path}/here", "/foo/bar/here"),
            ("{+path:6}/here", "/foo/b/here"),
            ("here?ref={+path}", "here?ref=/foo/bar"),
            ("up{+path}{var}/here", "up/foo/barvalue/here"),
            ("{+x,hello,y}", "1024,Hello%20World!,768"),
            ("{+path,x}/here", "/foo/bar,1024/here"),
            ("{+list}", "red,green,blue"),
            ("{+list*}", "red,green,blue"),
            (
                "{+keys}",
                [
                    "comma,,,dot,.,semi,;",
                    "comma,,,semi,;,dot,.",
                    "dot,.,comma,,,semi,;",
                    "dot,.,semi,;,comma,,",
                    "semi,;,comma,,,dot,.",
                    "semi,;,dot,.,comma,,",
                ],
            ),
            (
                "{+keys*}",
                [
                    "comma=,,dot=.,semi=;",
                    "comma=,,semi=;,dot=.",
                    "dot=.,comma=,,semi=;",
                    "dot=.,semi=;,comma=,",
                    "semi=;,comma=,,dot=.",
                    "semi=;,dot=.,comma=,",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_4_fragment_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.4 Fragment Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{#var}", "#value"),
            ("{#hello}", "#Hello%20World!"),
            ("{#half}", "#50%25"),
            ("foo{#empty}", "foo#"),
            ("foo{#undef}", "foo"),
            ("{#x,hello,y}", "#1024,Hello%20World!,768"),
            ("{#path,x}/here", "#/foo/bar,1024/here"),
            ("{#path:6}/here", "#/foo/b/here"),
            ("{#list}", "#red,green,blue"),
            ("{#list*}", "#red,green,blue"),
            (
                "{#keys}",
                [
                    "#comma,,,dot,.,semi,;",
                    "#comma,,,semi,;,dot,.",
                    "#dot,.,comma,,,semi,;",
                    "#dot,.,semi,;,comma,,",
                    "#semi,;,comma,,,dot,.",
                    "#semi,;,dot,.,comma,,",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_5_label_expansion_with_dot_prefix(self):
        """uritemplate test cases from RFC 6570 3.2.5 Label Expansion with Dot-Prefix"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{.who}", ".fred"),
            ("{.who,who}", ".fred.fred"),
            ("{.half,who}", ".50%25.fred"),
            ("www{.dom*}", "www.example.com"),
            ("X{.var}", "X.value"),
            ("X{.var:3}", "X.val"),
            ("X{.empty}", "X."),
            ("X{.undef}", "X"),
            ("X{.list}", "X.red,green,blue"),
            ("X{.list*}", "X.red.green.blue"),
            (
                "{#keys}",
                [
                    "#comma,,,dot,.,semi,;",
                    "#comma,,,semi,;,dot,.",
                    "#dot,.,comma,,,semi,;",
                    "#dot,.,semi,;,comma,,",
                    "#semi,;,comma,,,dot,.",
                    "#semi,;,dot,.,comma,,",
                ],
            ),
            (
                "{#keys*}",
                [
                    "#comma=,,dot=.,semi=;",
                    "#comma=,,semi=;,dot=.",
                    "#dot=.,comma=,,semi=;",
                    "#dot=.,semi=;,comma=,",
                    "#semi=;,comma=,,dot=.",
                    "#semi=;,dot=.,comma=,",
                ],
            ),
            ("X{.empty_keys}", "X"),
            ("X{.empty_keys*}", "X"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_6_path_segment_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.6 Path Segment Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{/who}", "/fred"),
            ("{/who,who}", "/fred/fred"),
            ("{/half,who}", "/50%25/fred"),
            ("{/who,dub}", "/fred/me%2Ftoo"),
            ("{/var}", "/value"),
            ("{/var,empty}", "/value/"),
            ("{/var,undef}", "/value"),
            ("{/var,x}/here", "/value/1024/here"),
            ("{/var:1,var}", "/v/value"),
            ("{/list}", "/red,green,blue"),
            ("{/list*}", "/red/green/blue"),
            ("{/list*,path:4}", "/red/green/blue/%2Ffoo"),
            (
                "{/keys}",
                [
                    "/comma,%2C,dot,.,semi,%3B",
                    "/comma,%2C,semi,%3B,dot,.",
                    "/dot,.,comma,%2C,semi,%3B",
                    "/dot,.,semi,%3B,comma,%2C",
                    "/semi,%3B,comma,%2C,dot,.",
                    "/semi,%3B,dot,.,comma,%2C",
                ],
            ),
            (
                "{/keys*}",
                [
                    "/comma=%2C/dot=./semi=%3B",
                    "/comma=%2C/semi=%3B/dot=.",
                    "/dot=./comma=%2C/semi=%3B",
                    "/dot=./semi=%3B/comma=%2C",
                    "/semi=%3B/comma=%2C/dot=.",
                    "/semi=%3B/dot=./comma=%2C",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_7_path_style_parameter_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.7 Path-Style Parameter Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{;who}", ";who=fred"),
            ("{;half}", ";half=50%25"),
            ("{;empty}", ";empty"),
            ("{;hello:5}", ";hello=Hello"),
            ("{;v,empty,who}", ";v=6;empty;who=fred"),
            ("{;v,bar,who}", ";v=6;who=fred"),
            ("{;x,y}", ";x=1024;y=768"),
            ("{;x,y,empty}", ";x=1024;y=768;empty"),
            ("{;x,y,undef}", ";x=1024;y=768"),
            ("{;list}", ";list=red,green,blue"),
            ("{;list*}", ";list=red;list=green;list=blue"),
            (
                "{;keys}",
                [
                    ";keys=comma,%2C,dot,.,semi,%3B",
                    ";keys=comma,%2C,semi,%3B,dot,.",
                    ";keys=dot,.,comma,%2C,semi,%3B",
                    ";keys=dot,.,semi,%3B,comma,%2C",
                    ";keys=semi,%3B,comma,%2C,dot,.",
                    ";keys=semi,%3B,dot,.,comma,%2C",
                ],
            ),
            (
                "{;keys*}",
                [
                    ";comma=%2C;dot=.;semi=%3B",
                    ";comma=%2C;semi=%3B;dot=.",
                    ";dot=.;comma=%2C;semi=%3B",
                    ";dot=.;semi=%3B;comma=%2C",
                    ";semi=%3B;comma=%2C;dot=.",
                    ";semi=%3B;dot=.;comma=%2C",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_8_form_style_query_expansion(self):
        """uritemplate test cases from RFC 6570 3.2.8 Form-Style Query Expansion"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{?who}", "?who=fred"),
            ("{?half}", "?half=50%25"),
            ("{?x,y}", "?x=1024&y=768"),
            ("{?x,y,empty}", "?x=1024&y=768&empty="),
            ("{?x,y,undef}", "?x=1024&y=768"),
            ("{?var:3}", "?var=val"),
            ("{?list}", "?list=red,green,blue"),
            ("{?list*}", "?list=red&list=green&list=blue"),
            (
                "{?keys}",
                [
                    "?keys=comma,%2C,dot,.,semi,%3B",
                    "?keys=comma,%2C,semi,%3B,dot,.",
                    "?keys=dot,.,comma,%2C,semi,%3B",
                    "?keys=dot,.,semi,%3B,comma,%2C",
                    "?keys=semi,%3B,comma,%2C,dot,.",
                    "?keys=semi,%3B,dot,.,comma,%2C",
                ],
            ),
            (
                "{?keys*}",
                [
                    "?comma=%2C&dot=.&semi=%3B",
                    "?comma=%2C&semi=%3B&dot=.",
                    "?dot=.&comma=%2C&semi=%3B",
                    "?dot=.&semi=%3B&comma=%2C",
                    "?semi=%3B&comma=%2C&dot=.",
                    "?semi=%3B&dot=.&comma=%2C",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_rfc6570_s3_2_9_form_style_query_continuation(self):
        """uritemplate test cases from RFC 6570 3.2.9 Form-Style Query Continuation"""
        variables = RFC6570_VARIABLES
        cases = [
            ("{&who}", "&who=fred"),
            ("{&half}", "&half=50%25"),
            ("?fixed=yes{&x}", "?fixed=yes&x=1024"),
            ("{&var:3}", "&var=val"),
            ("{&x,y,empty}", "&x=1024&y=768&empty="),
            ("{&x,y,undef}", "&x=1024&y=768"),
            ("{&list}", "&list=red,green,blue"),
            ("{&list*}", "&list=red&list=green&list=blue"),
            (
                "{&keys}",
                [
                    "&keys=comma,%2C,dot,.,semi,%3B",
                    "&keys=comma,%2C,semi,%3B,dot,.",
                    "&keys=dot,.,comma,%2C,semi,%3B",
                    "&keys=dot,.,semi,%3B,comma,%2C",
                    "&keys=semi,%3B,comma,%2C,dot,.",
                    "&keys=semi,%3B,dot,.,comma,%2C",
                ],
            ),
            (
                "{&keys*}",
                [
                    "&comma=%2C&dot=.&semi=%3B",
                    "&comma=%2C&semi=%3B&dot=.",
                    "&dot=.&comma=%2C&semi=%3B",
                    "&dot=.&semi=%3B&comma=%2C",
                    "&semi=%3B&comma=%2C&dot=.",
                    "&semi=%3B&dot=.&comma=%2C",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_1(self):
        """uritemplate-test Additional Examples 1"""
        variables = {
            "id": "person",
            "token": "12345",
            "fields": ["id", "name", "picture"],
            "format": "json",
            "q": "URI Templates",
            "page": "5",
            "lang": "en",
            "geocode": ["37.76", "-122.427"],
            "first_name": "John",
            "last.name": "Doe",
            "Some%20Thing": "foo",
            "number": 6,
            "long": 37.76,
            "lat": -122.427,
            "group_id": "12345",
            "query": "PREFIX dc: <http://purl.org/dc/elements/1.1/> SELECT ?book ?who WHERE { ?book dc:creator ?who }",
            "uri": "http://example.org/?uri=http%3A%2F%2Fexample.org%2F",
            "word": "drücken",
            "Stra%C3%9Fe": "Grüner Weg",
            "random": "šöäŸœñê€£¥‡ÑÒÓÔÕÖ×ØÙÚàáâãäåæçÿ",
            "assoc_special_chars": {"šöäŸœñê€£¥‡ÑÒÓÔÕ": "Ö×ØÙÚàáâãäåæçÿ"},
        }
        cases = [
            ("{/id*}", "/person"),
            (
                "{/id*}{?fields,first_name,last.name,token}",
                "/person?fields=id,name,picture&first_name=John&last.name=Doe&token=12345",
            ),
            (
                "/search.{format}{?q,geocode,lang,locale,page,result_type}",
                "/search.json?q=URI%20Templates&geocode=37.76,-122.427&lang=en&page=5",
            ),
            ("/test{/Some%20Thing}", "/test/foo"),
            ("/set{?number}", "/set?number=6"),
            ("/loc{?long,lat}", "/loc?long=37.76&lat=-122.427"),
            (
                "/base{/group_id,first_name}/pages{/page,lang}{?format,q}",
                "/base/12345/John/pages/5/en?format=json&q=URI%20Templates",
            ),
            (
                "/sparql{?query}",
                "/sparql?query=PREFIX%20dc%3A%20%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%3E%20SELECT%20%3Fbook%20%3Fwho%20WHERE%20%7B%20%3Fbook%20dc%3Acreator%20%3Fwho%20%7D",
            ),
            (
                "/go{?uri}",
                "/go?uri=http%3A%2F%2Fexample.org%2F%3Furi%3Dhttp%253A%252F%252Fexample.org%252F",
            ),
            ("/service{?word}", "/service?word=dr%C3%BCcken"),
            ("/lookup{?Stra%C3%9Fe}", "/lookup?Stra%C3%9Fe=Gr%C3%BCner%20Weg"),
            (
                "{random}",
                "%C5%A1%C3%B6%C3%A4%C5%B8%C5%93%C3%B1%C3%AA%E2%82%AC%C2%A3%C2%A5%E2%80%A1%C3%91%C3%92%C3%93%C3%94%C3%95%C3%96%C3%97%C3%98%C3%99%C3%9A%C3%A0%C3%A1%C3%A2%C3%A3%C3%A4%C3%A5%C3%A6%C3%A7%C3%BF",
            ),
            (
                "{?assoc_special_chars*}",
                "?%C5%A1%C3%B6%C3%A4%C5%B8%C5%93%C3%B1%C3%AA%E2%82%AC%C2%A3%C2%A5%E2%80%A1%C3%91%C3%92%C3%93%C3%94%C3%95=%C3%96%C3%97%C3%98%C3%99%C3%9A%C3%A0%C3%A1%C3%A2%C3%A3%C3%A4%C3%A5%C3%A6%C3%A7%C3%BF",
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_2(self):
        """uritemplate-test Additional Examples 2"""
        variables = {
            "id": ["person", "albums"],
            "token": "12345",
            "fields": ["id", "name", "picture"],
            "format": "atom",
            "q": "URI Templates",
            "page": "10",
            "start": "5",
            "lang": "en",
            "geocode": ["37.76", "-122.427"],
        }
        cases = [
            ("{/id*}", "/person/albums"),
            (
                "{/id*}{?fields,token}",
                "/person/albums?fields=id,name,picture&token=12345",
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_3_empty_variables(self):
        """uritemplate-test Additional Examples 3: Empty Variables"""
        variables = {"empty_list": [], "empty_assoc": {}}
        cases = [
            ("{/empty_list}", [""]),
            ("{/empty_list*}", [""]),
            ("{?empty_list}", [""]),
            ("{?empty_list*}", [""]),
            ("{?empty_assoc}", [""]),
            ("{?empty_assoc*}", [""]),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_4_numeric_keys(self):
        """uritemplate-test Additional Examples 4: Numeric Keys"""
        variables = {
            "42": "The Answer to the Ultimate Question of Life, the Universe, and Everything",
            "1337": ["leet", "as", "it", "can", "be"],
            "german": {"11": "elf", "12": "zwölf"},
        }
        cases = [
            (
                "{42}",
                "The%20Answer%20to%20the%20Ultimate%20Question%20of%20Life%2C%20the%20Universe%2C%20and%20Everything",
            ),
            (
                "{?42}",
                "?42=The%20Answer%20to%20the%20Ultimate%20Question%20of%20Life%2C%20the%20Universe%2C%20and%20Everything",
            ),
            ("{1337}", "leet,as,it,can,be"),
            ("{?1337*}", "?1337=leet&1337=as&1337=it&1337=can&1337=be"),
            ("{?german*}", ["?11=elf&12=zw%C3%B6lf", "?12=zw%C3%B6lf&11=elf"]),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_5_explode_combinations(self):
        """uritemplate-test Additional Examples 5: Explode Combinations"""
        variables = {
            "id": "admin",
            "token": "12345",
            "tab": "overview",
            "keys": {"key1": "val1", "key2": "val2"},
        }
        cases = [
            (
                "{?id,token,keys*}",
                [
                    "?id=admin&token=12345&key1=val1&key2=val2",
                    "?id=admin&token=12345&key2=val2&key1=val1",
                ],
            ),
            (
                "{/id}{?token,keys*}",
                [
                    "/admin?token=12345&key1=val1&key2=val2",
                    "/admin?token=12345&key2=val2&key1=val1",
                ],
            ),
            (
                "{?id,token}{&keys*}",
                [
                    "?id=admin&token=12345&key1=val1&key2=val2",
                    "?id=admin&token=12345&key2=val2&key1=val1",
                ],
            ),
            (
                "/user{/id}{?token,tab}{&keys*}",
                [
                    "/user/admin?token=12345&tab=overview&key1=val1&key2=val2",
                    "/user/admin?token=12345&tab=overview&key2=val2&key1=val1",
                ],
            ),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_6_reserved_expansion(self):
        """uritemplate-test Additional Examples 6: Reserved Expansion"""
        variables = {
            "id": "admin%2F",
            "not_pct": "%foo",
            "list": ["red%25", "%2Fgreen", "blue "],
            "keys": {"key1": "val1%2F", "key2": "val2%2F"},
        }
        cases = [
            ("{+id}", "admin%2F"),
            ("{#id}", "#admin%2F"),
            ("{id}", "admin%252F"),
            ("{+not_pct}", "%25foo"),
            ("{#not_pct}", "#%25foo"),
            ("{not_pct}", "%25foo"),
            ("{+list}", "red%25,%2Fgreen,blue%20"),
            ("{#list}", "#red%25,%2Fgreen,blue%20"),
            ("{list}", "red%2525,%252Fgreen,blue%20"),
            ("{+keys}", "key1,val1%2F,key2,val2%2F"),
            ("{#keys}", "#key1,val1%2F,key2,val2%2F"),
            ("{keys}", "key1,val1%252F,key2,val2%252F"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_7_prefix_modifiers_with_multibyte_characters(self):
        """uritemplate-test Additional Examples 7: Prefix Modifiers with Multibyte Characters"""
        variables = {
            "var": "value",
            "greek": "αβγδε",
            "currency": "€uro",
            "clef": "𝄞stave",
        }
        cases = [
            ("{greek:1}", "%CE%B1"),
            ("{greek:2}", "%CE%B1%CE%B2"),
            ("{+greek:2}", "%CE%B1%CE%B2"),
            ("{greek:30}", "%CE%B1%CE%B2%CE%B3%CE%B4%CE%B5"),
            ("{currency:1}", "%E2%82%AC"),
            ("{?currency:1}", "?currency=%E2%82%AC"),
            ("{clef:1}", "%F0%9D%84%9E"),
            ("{var:9999}", "value"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_extended_8_literal_encoding(self):
        """uritemplate-test Additional Examples 8: Literal Encoding"""
        variables = {"var": "value"}
        cases = [
            ("café/{var}", "caf%C3%A9/value"),
            ("x%20y/{var}", "x%20y/value"),
            ("x%20y{var}z%20w", "x%20yvaluez%20w"),
        ]
        for template, expected in cases:
            self.check(template, expected, variables)

    def test_invalid_templates(self):
        """uritemplate-test negative cases: malformed templates raise ValueError"""
        variables = {
            "id": "thing",
            "var": "value",
            "hello": "Hello World!",
            "with space": "fail",
            " leading_space": "Hi!",
            "trailing_space ": "Bye!",
            "empty": "",
            "path": "/foo/bar",
            "x": "1024",
            "y": "768",
            "list": ["red", "green", "blue"],
            "keys": {"semi": ";", "dot": ".", "comma": ","},
            "example": "red",
            "searchTerms": "uri templates",
            "~thing": "some-user",
            "default-graph-uri": [
                "http://www.example/book/",
                "http://www.example/papers/",
            ],
            "query": "PREFIX dc: <http://purl.org/dc/elements/1.1/> SELECT ?book ?who WHERE { ?book dc:creator ?who }",
        }
        templates = [
            "{/id*",
            "/id*}",
            "{/?id}",
            "{var:prefix}",
            "{hello:2*}",
            "{??hello}",
            "{!hello}",
            "{with space}",
            "{ leading_space}",
            "{trailing_space }",
            "{=path}",
            "{$var}",
            "{|var*}",
            "{*keys?}",
            "{?empty=default,var}",
            "{var}{-prefix|/-/|var}",
            "?q={searchTerms}&amp;c={example:color?}",
            "x{?empty|foo=none}",
            "/h{#hello+}",
            "/h#{hello+}",
            "{keys:1}",
            "{+keys:1}",
            "{;keys:1*}",
            "?{-join|&|var,list}",
            "/people/{~thing}",
            "/{default-graph-uri}",
            "/sparql{?query,default-graph-uri}",
            "/sparql{?query){&default-graph-uri*}",
            "/resolution{?x, y}",
            "{var:0}",
            "{var:01}",
            "{var:10000}",
            "{var:}",
            "{x.}",
            "{x..y}",
            "{%2x}",
        ]
        for template in templates:
            with self.assertRaises(ValueError, msg="%r" % template):
                uritemplate(template).expand(variables)
            with self.assertRaises(ValueError, msg="%r" % template):
                uritemplate(template.encode("utf-8")).expand(variables)

    def test_template_object(self):
        template = uritemplate("{+base}{/x*}")
        self.assertEqual(template.template, "{+base}{/x*}")
        self.assertEqual(str(template), "{+base}{/x*}")
        self.assertEqual(repr(template), "URITemplate('{+base}{/x*}')")
        self.assertEqual(uritemplate(b"{x}").template, "{x}")
        # a parsed template can be expanded repeatedly
        self.assertEqual(template.expand(base="http://a", x=["b", "c"]), "http://a/b/c")
        self.assertEqual(template.expand(base="http://d"), "http://d")
        self.assertEqual(template.expand(), "")
        # malformed templates are rejected when parsed
        with self.assertRaises(ValueError):
            uritemplate("{x")
        with self.assertRaises(AttributeError):
            template.parts = []  # type: ignore
        # templates of the wrong type are rejected when parsed
        for value in (None, 42, ["{x}"], bytearray(b"{x}")):
            with self.assertRaises(TypeError, msg="template=%r" % value):
                uritemplate(value)  # type: ignore

    def test_variables(self):
        # mapping, keyword arguments, and keyword arguments taking precedence
        self.assertEqual(uritemplate("{x}{?y}").expand(), "")
        self.assertEqual(uritemplate("{x}{?y}").expand({"x": 1, "y": 2}), "1?y=2")
        self.assertEqual(uritemplate("{x}{?y}").expand(x=1, y=2), "1?y=2")
        self.assertEqual(uritemplate("{x}{?y}").expand({"x": 1}, y=2), "1?y=2")
        self.assertEqual(uritemplate("{x}{?y}").expand({"x": 1, "y": 0}, y=2), "1?y=2")
        # names that are not Python identifiers
        self.assertEqual(
            uritemplate("{42}{?a.b}").expand({"42": 1, "a.b": 2}), "1?a.b=2"
        )

    def test_value_types(self):
        cases = [
            ("{x}", "a%20b", {"x": "a b"}),
            ("{x}", "a%20b", {"x": b"a b"}),
            ("{x}", "%C3%A4", {"x": "\xe4"}),
            ("{x}", "%C3%A4", {"x": b"\xc3\xa4"}),
            ("{x}", "42", {"x": 42}),
            ("{x}", "4.2", {"x": 4.2}),
            ("{x}", "True", {"x": True}),
            ("{x}", "a,1,%C3%A4", {"x": ["a", 1, b"\xc3\xa4"]}),
            ("{x}", "a,1", {"x": ("a", 1)}),
            ("{x}", "a,1,b,2", {"x": {"a": 1, b"b": "2"}}),
            ("{x*}", "a=1,b=2", {"x": {"a": 1, b"b": "2"}}),
            ("{x:2}", "%C3%A4%C3%B6", {"x": "\xe4\xf6\xfc"}),
            ("{x:2}", "%C3%A4", {"x": b"\xc3\xa4\xc3\xb6"}),
            ("{x:1}", "4", {"x": 42}),
        ]
        for template, expected, variables in cases:
            self.check(template, expected, variables)
        # any iterable is accepted, and consumed only once
        self.assertEqual(uritemplate("{x}").expand({"x": iter(["a", 1])}), "a,1")
        for value in (object(), [object()], {"a": object()}, [["nested"]]):
            with self.assertRaises(TypeError, msg="%r" % (value,)):
                uritemplate("{x}").expand({"x": value})  # type: ignore

    def test_undefined_values(self):
        cases = [
            ("a{x}b", "ab", {"x": None}),
            ("a{x}b", "ab", {"x": []}),
            ("a{x}b", "ab", {"x": {}}),
            ("a{x}b", "ab", {"x": [None, None]}),
            ("a{x}b", "ab", {"x": {"a": None}}),
            ("a{x}b", "aab", {"x": [None, "a", None]}),
            ("a{x}b", "aa,1b", {"x": {"a": 1, "b": None}}),
            ("a{x*}b", "aa=1b", {"x": {"a": 1, "b": None}}),
            ("a{?x}b", "a?x=a,1b", {"x": {"a": 1, "b": None}}),
            ("a{?x*}b", "a?a=1b", {"x": {"a": 1, "b": None}}),
            ("a{?x,y}b", "a?y=1b", {"x": [], "y": 1}),
        ]
        for template, expected, variables in cases:
            self.check(template, expected, variables)

    def test_empty_values(self):
        # RFC 6570 3.2.1: "ifemp" handling for empty strings
        cases = [
            ("{x}", "", {"x": ""}),
            ("{;x}", ";x", {"x": ""}),
            ("{?x}", "?x=", {"x": ""}),
            ("{&x}", "&x=", {"x": ""}),
            ("{;x}", ";x", {"x": [""]}),
            ("{;x*}", ";x", {"x": [""]}),
            ("{?x*}", "?x=", {"x": [""]}),
            ("{/x*}", "/", {"x": [""]}),
            ("{;x*}", ";a", {"x": {"a": ""}}),
            ("{?x*}", "?a=", {"x": {"a": ""}}),
            ("{/x*}", "/a=", {"x": {"a": ""}}),
            ("{x*}", "a=", {"x": {"a": ""}}),
        ]
        for template, expected, variables in cases:
            self.check(template, expected, variables)

    def test_literals(self):
        cases = [
            ("", "", {}),
            ("/foo/bar", "/foo/bar", {}),
            ("caf\xe9", "caf%C3%A9", {}),
            ("a b", "a%20b", {}),
            ("%41%zz%", "%41%25zz%25", {}),
            ("?q=1&r=2#f", "?q=1&r=2#f", {}),
        ]
        for template, expected, variables in cases:
            self.check(template, expected, variables)
