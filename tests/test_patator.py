import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from patator import patator as pt


class _DummyLogger:
    def __init__(self):
        self.debug_messages = []
        self.warn_messages = []
        self.info_messages = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def warn(self, msg):
        self.warn_messages.append(msg)

    def info(self, msg):
        self.info_messages.append(msg)


class PatatorUtilsTests(unittest.TestCase):
    def test_b_and_B_roundtrip(self):
        self.assertEqual(pt.b("abc"), b"abc")
        self.assertEqual(pt.B(b"abc"), "abc")
        self.assertEqual(pt.b(b"\xff"), b"\xff")
        self.assertEqual(pt.B("text"), "text")

    def test_repr23_ascii_and_binary(self):
        self.assertEqual(pt.repr23("abcXYZ123"), "abcXYZ123")
        self.assertEqual(pt.repr23("\x00A"), "'\\x00A'")

    def test_ppstr_and_flatten(self):
        self.assertEqual(pt.ppstr(b"line\r\n"), "line")
        self.assertEqual(pt.ppstr(123), "123")
        self.assertEqual(pt.flatten([b"a\r\n", ("b\n", 3), "c"]), ["a", "b", "3", "c"])

    def test_parse_query_keeps_plus_sign(self):
        out = pt.parse_query("a=1+2&b=hello%2Bworld")
        self.assertEqual(out, [("a", "1+2"), ("b", "hello+world")])

    def test_parse_query_keep_blank_values(self):
        out = pt.parse_query("a=&b", keep_blank_values=True)
        self.assertEqual(out, [("a", ""), ("b", "")])

    def test_hash_helpers(self):
        self.assertEqual(pt.md5hex(b"abc"), "900150983cd24fb0d6963f7d28e17f72")
        self.assertEqual(pt.sha1hex(b"abc"), "a9993e364706816aba3e25717850c26c9cd0d89d")

    def test_padhex_and_pprint_seconds(self):
        self.assertEqual(pt.padhex(0xA), "0a")
        self.assertEqual(pt.padhex(0xAB), "ab")
        self.assertEqual(pt.pprint_seconds(3661, "%d:%02d:%02d"), "1:01:01")

    def test_count_lines(self):
        with tempfile.NamedTemporaryFile("wb", delete=False) as fh:
            path = fh.name
            fh.write(b"one\n")
            fh.write(b"two\n")
            fh.write(b"three")
        try:
            self.assertEqual(pt.count_lines(path), 2)
        finally:
            os.unlink(path)


class PatatorFilesystemTests(unittest.TestCase):
    def test_create_dir_makes_directory(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "logs"
            out = pt.create_dir(str(dst), assume_yes=True)
            self.assertEqual(Path(out), dst.resolve())
            self.assertTrue(dst.is_dir())

    def test_create_dir_wipes_existing_files(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td)
            f = dst / "old.txt"
            f.write_text("x", encoding="utf-8")
            out = pt.create_dir(str(dst), assume_yes=True)
            self.assertEqual(Path(out), dst.resolve())
            self.assertFalse(f.exists())

    def test_create_dir_aborts_when_subdirectories_exist(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td)
            (dst / "sub").mkdir()
            with self.assertRaises(SystemExit):
                pt.create_dir(str(dst), assume_yes=True)

    def test_create_time_dir_structure(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(pt.create_time_dir(td, "scan"))
            self.assertTrue(out.is_dir())
            self.assertIn("scan", out.name)


class PatatorIterationTests(unittest.TestCase):
    def test_product_and_chain(self):
        self.assertEqual(list(pt.product([1, 2], ["a"])), [[1, "a"], [2, "a"]])
        self.assertEqual(list(pt.chain([1, 2], [3])), [1, 2, 3])

    def test_rangeiter_int_forward_and_backward(self):
        self.assertEqual(list(pt.RangeIter("int", "1-3")), ["1", "2", "3"])
        self.assertEqual(list(pt.RangeIter("int", "3-1")), ["3", "2", "1"])

    def test_rangeiter_hex_and_float(self):
        self.assertEqual(list(pt.RangeIter("hex", "0x1-0x3")), ["01", "02", "03"])
        self.assertEqual(list(pt.RangeIter("float", "1.1-1.3")), ["1.1", "1.2", "1.3"])

    def test_rangeiter_letters(self):
        self.assertEqual(list(pt.RangeIter("lower", "a-c")), ["a", "b", "c"])
        self.assertEqual(len(pt.RangeIter("lower", "a-c")), 3)

    def test_rangeiter_random_mode_len_is_maxint(self):
        r = pt.RangeIter("int", "1-3", random=True)
        self.assertEqual(len(r), pt.maxint)

    def test_rangeiter_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            pt.RangeIter("bad", "1-2")
        with self.assertRaises(ValueError):
            pt.RangeIter("int", "invalid")


class PatatorResponseTests(unittest.TestCase):
    def test_match_range(self):
        self.assertTrue(pt.match_range(5, "5"))
        self.assertTrue(pt.match_range(5, "1-10"))
        self.assertTrue(pt.match_range(5, "-5"))
        self.assertTrue(pt.match_range(5, "5-"))
        self.assertFalse(pt.match_range(5, "6"))
        with self.assertRaises(ValueError):
            pt.match_range(5, "-")
        with self.assertRaises(ValueError):
            pt.match_range(5, "10-5")

    def test_response_base_matching_and_dump(self):
        r = pt.Response_Base(200, "hello world", timing=1.5, trace="trace")
        self.assertEqual(r.indicators(), (200, 11, "1.500"))
        self.assertTrue(r.match("code", "2\\d\\d"))
        self.assertTrue(r.match("size", "11"))
        self.assertTrue(r.match("time", "1-2"))
        self.assertTrue(r.match("mesg", "hello world"))
        self.assertTrue(r.match("fgrep", "world"))
        self.assertTrue(r.match("egrep", r"hello\s+\w+"))
        self.assertEqual(r.dump(), b"trace")
        self.assertEqual(r.str_target(), "")

    def test_response_http_behaviors(self):
        mesg = "HTTP/1.1 302 Found\r\nx: y\r\n\r\nbody"
        r = pt.Response_HTTP(302, mesg, timing=0.25, content_length=4, target={"ip": "1.1.1.1"})
        self.assertEqual(r.indicators(), (302, "32:4", "0.250"))
        self.assertEqual(str(r), "HTTP/1.1 302 Found")
        self.assertTrue(r.match_clen("4"))
        self.assertTrue(r.match_egrep("^HTTP/1.1 302"))
        self.assertIn("ip=", r.str_target())

    def test_response_ajp_string_is_first_line(self):
        r = pt.Response_AJP(200, "HTTP/1.1 200 OK\r\nHeader: v\r\n\r\nbody")
        self.assertEqual(str(r), "HTTP/1.1 200 OK")

    def test_split_ntlm(self):
        self.assertEqual(pt.split_ntlm("aa:bb"), ("aa", "bb"))
        self.assertEqual(
            pt.split_ntlm("bb"),
            ("aad3b435b51404eeaad3b435b51404ee", "bb"),
        )
        self.assertEqual(pt.split_ntlm(None), ("", ""))


class PatatorControllerAndCacheTests(unittest.TestCase):
    def setUp(self):
        self._old_logger = getattr(pt, "logger", None)
        pt.logger = _DummyLogger()

    def tearDown(self):
        if self._old_logger is None and hasattr(pt, "logger"):
            delattr(pt, "logger")
        else:
            pt.logger = self._old_logger

    def _controller(self):
        c = pt.Controller.__new__(pt.Controller)
        c.ns = SimpleNamespace(actions={}, free_list=[], skip_list=[])
        c.condition_delim = ","
        c.available_actions = [k for k, _ in pt.Controller.builtin_actions]
        return c

    def test_controller_key_finders(self):
        c = self._controller()
        self.assertEqual(list(c.find_file_keys("xFILE1y")), [1])
        self.assertEqual(list(c.find_net_keys("NET3")), [3])
        self.assertEqual([tuple(x) for x in c.find_combo_keys("COMBO12")], [(1, 2)])
        self.assertEqual(list(c.find_module_keys("MOD4")), [4])
        self.assertEqual(list(c.find_range_keys("RANGE5")), [5])
        self.assertEqual(list(c.find_prog_keys("PROG6")), [6])
        self.assertEqual(list(c.expand_key("k=v")), [["k", "v"]])

    def test_controller_action_registration_and_lookup(self):
        c = self._controller()
        c.update_actions("ignore,retry:code=200,fgrep=ok")
        self.assertIn("ignore", c.ns.actions)
        self.assertIn("retry", c.ns.actions)

        class _Resp:
            def match(self, key, val):
                checks = {
                    ("code", "200"): True,
                    ("fgrep", "ok"): True,
                }
                return checks[(key, val)]

        acts = c.lookup_actions(_Resp())
        self.assertEqual(set(acts), {"ignore", "retry"})

    def test_controller_action_lookup_with_negation(self):
        c = self._controller()
        c.update_actions("ignore:fgrep!=bad")
        seen = {}

        class _Resp:
            def match(self, key, val):
                seen["kv"] = (key, val)
                return False

        acts = c.lookup_actions(_Resp())
        self.assertEqual(seen["kv"], ("fgrep", "bad"))
        self.assertEqual(set(acts), {"ignore"})

    def test_controller_register_and_should_free_skip(self):
        c = self._controller()
        payload = {"host": "10.0.0.1", "user": "admin"}
        prod = ["10.0.0.1", "admin"]
        c.register_free(payload, "host+user")
        c.register_skip(prod, "0+1")
        self.assertTrue(c.should_free(payload))
        self.assertTrue(c.should_skip(prod))

    def test_controller_update_actions_rejects_unknown_action(self):
        c = self._controller()
        with self.assertRaises(ValueError):
            c.update_actions("unsupported:code=200")

    def test_tcp_cache_bind_reuses_connection_and_reset_closes(self):
        class _Conn:
            def __init__(self, fp, banner):
                self.fp = fp
                self.banner = banner
                self.closed = False

            def close(self):
                self.closed = True

        class _Cache(pt.TCP_Cache):
            def __init__(self):
                super().__init__()
                self.connect_calls = 0

            def connect(self, host, port, *args, **kwargs):
                self.connect_calls += 1
                return _Conn(fp=f"{host}:{port}", banner="hello")

        c = _Cache()
        fp1, banner1 = c.bind("h", 1, "user")
        fp2, banner2 = c.bind("h", 1, "user")
        self.assertEqual((fp1, banner1), ("h:1", "hello"))
        self.assertEqual((fp2, banner2), ("h:1", "hello"))
        self.assertEqual(c.connect_calls, 1)
        c.reset()
        self.assertEqual(c.curr, None)
        self.assertEqual(c.cache, {})


class PatatorFeatureTests(unittest.TestCase):
    def setUp(self):
        self._old_logger = getattr(pt, "logger", None)
        pt.logger = _DummyLogger()

    def tearDown(self):
        if self._old_logger is None and hasattr(pt, "logger"):
            delattr(pt, "logger")
        else:
            pt.logger = self._old_logger

    def test_generate_tld(self):
        tlds, size = pt.generate_tld()
        self.assertEqual(size, len(tlds))
        self.assertIn("com", tlds)
        self.assertIn("fr", tlds)

    def test_generate_srv_handles_missing_system_files(self):
        with patch("os.path.isfile", return_value=False):
            srv, size = pt.generate_srv()
        self.assertEqual(size, len(srv))
        self.assertIn("_ldap._tcp", srv)
        self.assertEqual(len(pt.logger.warn_messages), 4)

    def test_generate_transforms(self):
        transforms, total = pt.generate_transforms()
        data = list(transforms)
        self.assertEqual(total, len(data))
        self.assertIn("5,1,1,1", data)

    def test_generate_tst(self):
        vals, size = pt.generate_tst()
        self.assertEqual(vals, ["prd", "dev"])
        self.assertEqual(size, 2)

    def test_vnc_gen_key(self):
        v = pt.VNC()
        self.assertEqual(v.gen_key("A"), b"\x82")
        self.assertEqual(v.gen_key("\x00"), b"\x00")

    def test_umbraco_crack_success_and_failure(self):
        u = pt.Umbraco_crack()
        pwd = "Password1"
        p = pwd.encode("utf-16-le")
        h = pt.B(pt.b64encode(pt.hmac.new(p, p, digestmod=pt.hashlib.sha1).digest()))
        ok = u.execute(password=pwd, hashlist=f"user:{h}\n")
        bad = u.execute(password=pwd, hashlist="user:nomatch\n")
        self.assertEqual(ok.code, 0)
        self.assertIn(h, ok.mesg)
        self.assertEqual(bad.code, 1)

    def test_dns_query_uses_udp_and_tcp_fallback_when_truncated(self):
        class _Resp:
            def __init__(self, flags):
                self.flags = flags

        calls = []
        fake_dns = SimpleNamespace(
            message=SimpleNamespace(make_query=lambda qname, qtype, qclass: ("req", qname, qtype, qclass)),
            query=SimpleNamespace(
                udp=lambda request, server, timeout, one_rr_per_rrset: (calls.append("udp"), _Resp(flags=1))[1],
                tcp=lambda request, server, timeout, one_rr_per_rrset: (calls.append("tcp"), _Resp(flags=0))[1],
            ),
            flags=SimpleNamespace(TC=1),
        )
        with patch.object(pt, "dns", fake_dns, create=True):
            pt.dns_query("8.8.8.8", 1, "udp", "example.com", "A", "IN")
        self.assertEqual(calls, ["udp", "tcp"])

    def test_dns_query_tcp_only(self):
        calls = []
        fake_dns = SimpleNamespace(
            message=SimpleNamespace(make_query=lambda qname, qtype, qclass: ("req", qname, qtype, qclass)),
            query=SimpleNamespace(
                udp=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("udp not expected")),
                tcp=lambda request, server, timeout, one_rr_per_rrset: (calls.append("tcp"), SimpleNamespace(flags=0))[1],
            ),
            flags=SimpleNamespace(TC=1),
        )
        with patch.object(pt, "dns", fake_dns, create=True):
            pt.dns_query("8.8.8.8", 1, "tcp", "example.com", "A", "IN")
        self.assertEqual(calls, ["tcp"])

    @unittest.skipUnless(hasattr(pt, "AjpForwardRequest"), "ajpy is not installed")
    def test_prepare_ajp_forward_request(self):
        req = pt.prepare_ajp_forward_request("example.com", "/a?b=1", pt.AjpForwardRequest.REQUEST_METHODS.get("GET"))
        self.assertEqual(req.server_name, "example.com")
        self.assertEqual(req.req_uri, "/a?b=1")
        self.assertIn("SC_REQ_HOST", req.request_headers)


class PatatorCliTests(unittest.TestCase):
    def test_show_usage_exits_with_code_2(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            with self.assertRaises(SystemExit) as exc:
                pt.show_usage()
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("Available modules", out.getvalue())

    def test_cli_aborts_when_dependency_missing_for_target_module(self):
        class _FakeCtrl:
            def __init__(self, module, argv):
                pass

            def fire(self):
                raise AssertionError("should not fire")

        class _FakeModule:
            pass

        with patch.object(pt, "modules", [("fake", (_FakeCtrl, _FakeModule))]), patch.object(
            pt, "notfound", ["missingdep"]
        ), patch.object(
            pt, "dependencies",
            {"missingdep": [("fake",), "http://example.invalid", "1.0"]},
        ), patch.object(
            sys, "argv", ["fake"]
        ), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out:
            with self.assertRaises(SystemExit) as exc:
                pt.cli()
        self.assertEqual(exc.exception.code, 3)
        self.assertIn("is required to run fake", out.getvalue())

    def test_cli_starts_selected_module(self):
        called = {}

        class _FakeCtrl:
            def __init__(self, module, argv):
                called["module"] = module
                called["argv"] = list(argv)

            def fire(self):
                called["fired"] = True

        class _FakeModule:
            pass

        with patch.object(pt, "modules", [("fake", (_FakeCtrl, _FakeModule))]), patch.object(
            pt, "notfound", []
        ), patch.object(
            sys, "argv", ["fake"]
        ):
            pt.cli()

        self.assertIs(called["module"], _FakeModule)
        self.assertEqual(called["argv"], ["fake"])
        self.assertTrue(called["fired"])


if __name__ == "__main__":
    unittest.main()
