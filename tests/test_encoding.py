import unittest

from uritools import RESERVED, UNRESERVED, uridecode, uriencode


class EncodingTest(unittest.TestCase):
    def check(self, decoded, encoded, safe="", encoding="utf-8"):
        self.assertEqual(uriencode(decoded, safe, encoding), encoded)
        self.assertEqual(uridecode(encoded, encoding), decoded)
        # swap bytes/string types
        self.assertEqual(uriencode(decoded.encode(encoding), safe, encoding), encoded)
        self.assertEqual(uridecode(encoded.decode("ascii"), encoding), decoded)

    def test_encoding(self):
        cases = [
            ("", b""),
            (" ", b"%20"),
            ("%", b"%25"),
            ("~", b"~"),
            (UNRESERVED, UNRESERVED.encode("ascii")),
        ]
        for decoded, encoded in cases:
            self.check(decoded, encoded)

    def test_safe_encoding(self):
        cases = [
            ("", b"", ""),
            ("", b"", b""),
            (" ", b" ", " "),
            (" ", b" ", b" "),
            ("%", b"%", "%"),
            ("%", b"%", b"%"),
            (RESERVED, RESERVED.encode("ascii"), RESERVED),
        ]
        for decoded, encoded, safe in cases:
            self.check(decoded, encoded, safe)

    def test_safe_cache(self):
        # results stay correct for many distinct `safe` values, beyond the
        # size of the internal per-`safe` lookup table cache
        unreserved = UNRESERVED.encode("ascii")
        safes = [bytes([i]) for i in range(1, 256) if bytes([i]) not in unreserved]
        for safe in safes:
            self.assertEqual(uriencode(b"\x00" + safe, safe), b"%00" + safe)
            self.assertEqual(uriencode(b"\x00" + safe), b"%00" + uriencode(safe))
        for safe in safes:
            self.assertEqual(uriencode(safe, safe), safe)

    def test_utf8_encoding(self):
        cases = [("\xf6lk\xfcrbis", b"%C3%B6lk%C3%BCrbis")]
        for decoded, encoded in cases:
            self.check(decoded, encoded, encoding="utf-8")

    def test_latin1_encoding(self):
        cases = [("\xf6lk\xfcrbis", b"%F6lk%FCrbis")]
        for decoded, encoded in cases:
            self.check(decoded, encoded, encoding="latin-1")

    def test_idna_encoding(self):
        cases = [("\xf6lk\xfcrbis", b"xn--lkrbis-vxa4c")]
        for decoded, encoded in cases:
            self.check(decoded, encoded, encoding="idna")

    def test_decode_bytes(self):
        cases = [
            ("%F6lk%FCrbis", b"\xf6lk\xfcrbis"),
            (b"%F6lk%FCrbis", b"\xf6lk\xfcrbis"),
        ]
        for uristring, expected in cases:
            self.assertEqual(uridecode(uristring, encoding=None), expected)

    def test_encode_bytes(self):
        cases = [(b"\xf6lk\xfcrbis", b"%F6lk%FCrbis")]
        for uristring, expected in cases:
            self.assertEqual(uriencode(uristring, encoding=None), expected)

    def test_decode_errors(self):
        cases = [
            (UnicodeError, b"%FF", "utf-8"),
        ]
        for exception, string, encoding in cases:
            self.assertRaises(exception, uridecode, string, encoding)

    def test_encode_errors(self):
        cases = [
            (UnicodeError, "\xff", b"", "ascii"),
        ]
        for exception, string, safe, encoding in cases:
            self.assertRaises(exception, uriencode, string, safe, encoding)
