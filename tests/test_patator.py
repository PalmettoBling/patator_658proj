"""
Comprehensive test suite for patator.py

Run with: python -m pytest tests/ -v
"""

import sys
import os
import re
import time as time_module
import hashlib
import logging
import platform
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import patator.patator as pat


# ---------------------------------------------------------------------------
# b() / B() -- bytes / str coercion helpers
# ---------------------------------------------------------------------------

class TestBytesConversion:
    def test_b_bytes_returns_same_object(self):
        data = b'hello'
        assert pat.b(data) is data

    def test_b_str_encodes_iso8859(self):
        assert pat.b('hello') == b'hello'

    def test_b_returns_bytes_type(self):
        assert isinstance(pat.b('test'), bytes)

    def test_b_latin1_high_bytes(self):
        assert pat.b('\xff\xfe') == b'\xff\xfe'

    def test_b_non_latin1_chars_ignored(self):
        result = pat.b('\u4e2d\u6587')
        assert isinstance(result, bytes)

    def test_B_str_returns_same_object(self):
        s = 'hello'
        assert pat.B(s) is s

    def test_B_bytes_decodes_iso8859(self):
        assert pat.B(b'hello') == 'hello'

    def test_B_returns_str_type(self):
        assert isinstance(pat.B(b'test'), str)

    def test_B_high_bytes_decoded(self):
        result = pat.B(b'\xff\xfe')
        assert isinstance(result, str)
        assert len(result) == 2

    def test_b_B_ascii_roundtrip(self):
        assert pat.B(pat.b('hello world')) == 'hello world'


# ---------------------------------------------------------------------------
# ppstr() -- pretty-print string (strips trailing \r\n)
# ---------------------------------------------------------------------------

class TestPpstr:
    def test_bytes_strips_crlf(self):
        assert pat.ppstr(b'hello\r\n') == 'hello'

    def test_str_strips_crlf(self):
        assert pat.ppstr('hello\r\n') == 'hello'

    def test_strips_trailing_newline_only(self):
        assert pat.ppstr('line\n') == 'line'

    def test_strips_trailing_cr_only(self):
        assert pat.ppstr('line\r') == 'line'

    def test_clean_string_unchanged(self):
        assert pat.ppstr('clean') == 'clean'

    def test_int_converts_to_str(self):
        assert pat.ppstr(42) == '42'

    def test_empty_string(self):
        assert pat.ppstr('') == ''

    def test_non_string_object_converted(self):
        assert isinstance(pat.ppstr([1, 2]), str)


# ---------------------------------------------------------------------------
# flatten() -- flatten a list, coercing items to stripped strings
# ---------------------------------------------------------------------------

class TestFlatten:
    def test_flat_list_of_strings(self):
        assert pat.flatten(['a', 'b', 'c']) == ['a', 'b', 'c']

    def test_nested_list_expanded(self):
        assert pat.flatten([['a', 'b'], 'c']) == ['a', 'b', 'c']

    def test_nested_tuple_expanded(self):
        assert pat.flatten([('x', 'y'), 'z']) == ['x', 'y', 'z']

    def test_bytes_stripped_and_decoded(self):
        assert pat.flatten([b'hello\r\n']) == ['hello']

    def test_int_converted_to_str(self):
        assert pat.flatten([42]) == ['42']

    def test_mixed_types(self):
        assert pat.flatten([42, 'str', b'bytes\n']) == ['42', 'str', 'bytes']

    def test_empty_list(self):
        assert pat.flatten([]) == []

    def test_nested_bytes_tuple(self):
        assert pat.flatten([(b'a\n', b'b\n')]) == ['a', 'b']


# ---------------------------------------------------------------------------
# pprint_seconds() -- format elapsed seconds as Nh Nm Ns
# ---------------------------------------------------------------------------

class TestPprintSeconds:
    def test_zero_seconds(self):
        assert pat.pprint_seconds(0, '%dh %dm %ds') == '0h 0m 0s'

    def test_one_minute(self):
        assert pat.pprint_seconds(60, '%dh %dm %ds') == '0h 1m 0s'

    def test_one_hour(self):
        assert pat.pprint_seconds(3600, '%dh %dm %ds') == '1h 0m 0s'

    def test_complex_time(self):
        assert pat.pprint_seconds(3661, '%dh %dm %ds') == '1h 1m 1s'

    def test_ninety_seconds(self):
        assert pat.pprint_seconds(90, '%dh %dm %ds') == '0h 1m 30s'

    def test_two_hours(self):
        assert pat.pprint_seconds(7200, '%dh %dm %ds') == '2h 0m 0s'


# ---------------------------------------------------------------------------
# repr23() -- safe repr (returns printable ASCII as-is, otherwise repr)
# ---------------------------------------------------------------------------

class TestRepr23:
    def test_printable_ascii_returned_as_is(self):
        assert pat.repr23('hello world') == 'hello world'

    def test_digits_returned_as_is(self):
        assert pat.repr23('12345') == '12345'

    def test_space_is_printable(self):
        assert pat.repr23('a b c') == 'a b c'

    def test_null_byte_triggers_repr(self):
        result = pat.repr23('\x00')
        assert '\\x00' in result

    def test_control_char_triggers_repr(self):
        result = pat.repr23('abc\x01')
        assert '\\x01' in result

    def test_del_char_triggers_repr(self):
        # 0x7f is outside printable range
        result = pat.repr23('\x7f')
        assert result != '\x7f'

    def test_high_byte_triggers_repr(self):
        result = pat.repr23('\xff')
        assert isinstance(result, str)
        assert result != '\xff'

    def test_repr_result_is_str(self):
        assert isinstance(pat.repr23('\x00'), str)


# ---------------------------------------------------------------------------
# md5hex() / sha1hex() -- hex digest helpers
# ---------------------------------------------------------------------------

class TestHashFunctions:
    def test_md5hex_known_value(self):
        assert pat.md5hex(b'hello') == hashlib.md5(b'hello').hexdigest()

    def test_sha1hex_known_value(self):
        assert pat.sha1hex(b'hello') == hashlib.sha1(b'hello').hexdigest()

    def test_md5hex_empty(self):
        assert pat.md5hex(b'') == 'd41d8cd98f00b204e9800998ecf8427e'

    def test_sha1hex_empty(self):
        assert pat.sha1hex(b'') == 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    def test_md5hex_is_32_hex_chars(self):
        assert re.match(r'^[0-9a-f]{32}$', pat.md5hex(b'test'))

    def test_sha1hex_is_40_hex_chars(self):
        assert re.match(r'^[0-9a-f]{40}$', pat.sha1hex(b'test'))

    def test_different_inputs_produce_different_hashes(self):
        assert pat.md5hex(b'a') != pat.md5hex(b'b')
        assert pat.sha1hex(b'a') != pat.sha1hex(b'b')


# ---------------------------------------------------------------------------
# padhex() -- zero-pad a number to an even-length hex string
# ---------------------------------------------------------------------------

class TestPadhex:
    def test_zero_padded_to_two(self):
        assert pat.padhex(0) == '00'

    def test_one_padded_to_two(self):
        assert pat.padhex(1) == '01'

    def test_fifteen_padded(self):
        assert pat.padhex(15) == '0f'

    def test_255_no_padding_needed(self):
        assert pat.padhex(255) == 'ff'

    def test_256_three_digits_padded_to_four(self):
        # 256 = 0x100 (3 hex digits → padded to 4)
        assert pat.padhex(256) == '0100'

    def test_65535_no_padding(self):
        assert pat.padhex(65535) == 'ffff'

    def test_result_always_even_length(self):
        for n in range(300):
            assert len(pat.padhex(n)) % 2 == 0, f'padhex({n}) has odd length'


# ---------------------------------------------------------------------------
# parse_query() -- URL query-string parser that preserves '+'
# ---------------------------------------------------------------------------

class TestParseQuery:
    def test_single_pair(self):
        assert pat.parse_query('a=1') == [('a', '1')]

    def test_multiple_ampersand_pairs(self):
        assert pat.parse_query('a=1&b=2') == [('a', '1'), ('b', '2')]

    def test_url_encoded_value_decoded(self):
        assert pat.parse_query('a=hello%20world') == [('a', 'hello world')]

    def test_plus_not_replaced_with_space(self):
        # Intentionally different from urllib.parse.parse_qsl
        assert pat.parse_query('a=hello+world') == [('a', 'hello+world')]

    def test_empty_value_excluded_by_default(self):
        assert pat.parse_query('a=') == []

    def test_keep_blank_values_includes_empty(self):
        assert pat.parse_query('a=', keep_blank_values=True) == [('a', '')]

    def test_key_without_equals_skipped(self):
        assert pat.parse_query('no_value') == []

    def test_semicolon_separator_supported(self):
        assert pat.parse_query('a=1;b=2') == [('a', '1'), ('b', '2')]

    def test_empty_string_returns_empty(self):
        assert pat.parse_query('') == []

    def test_split_on_first_equals_only(self):
        assert pat.parse_query('key=val=ue') == [('key', 'val=ue')]


# ---------------------------------------------------------------------------
# product() -- memory-efficient cartesian product (yields lists, not tuples)
# ---------------------------------------------------------------------------

class TestProduct:
    def test_single_list_wraps_each_item(self):
        assert list(pat.product([1, 2, 3])) == [[1], [2], [3]]

    def test_two_lists_cartesian(self):
        result = list(pat.product([1, 2], ['a', 'b']))
        assert result == [[1, 'a'], [1, 'b'], [2, 'a'], [2, 'b']]

    def test_empty_list_returns_empty(self):
        assert list(pat.product([])) == []

    def test_three_lists(self):
        assert list(pat.product([1], [2], [3])) == [[1, 2, 3]]

    def test_yields_lists_not_tuples(self):
        result = list(pat.product([1]))
        assert isinstance(result[0], list)

    def test_two_by_three_count(self):
        assert len(list(pat.product([1, 2], ['a', 'b', 'c']))) == 6

    def test_order_lexicographic(self):
        result = list(pat.product([0, 1], [0, 1]))
        assert result[0] == [0, 0]
        assert result[-1] == [1, 1]


# ---------------------------------------------------------------------------
# chain -- iterable concatenation (re-iterable unlike itertools.chain)
# ---------------------------------------------------------------------------

class TestChain:
    def test_two_iterables(self):
        assert list(pat.chain([1, 2], [3, 4])) == [1, 2, 3, 4]

    def test_single_iterable(self):
        assert list(pat.chain([1, 2, 3])) == [1, 2, 3]

    def test_empty_iterables(self):
        assert list(pat.chain([], [])) == []

    def test_string_chars_yielded(self):
        assert list(pat.chain('ab', 'cd')) == ['a', 'b', 'c', 'd']

    def test_can_iterate_multiple_times(self):
        c = pat.chain([1], [2])
        assert list(c) == list(c) == [1, 2]

    def test_mixed_types(self):
        assert list(pat.chain([1, 'two'], [3.0])) == [1, 'two', 3.0]


# ---------------------------------------------------------------------------
# RangeIter -- int type
# ---------------------------------------------------------------------------

class TestRangeIterInt:
    def test_ascending_range(self):
        assert list(pat.RangeIter('int', '1-3')) == ['1', '2', '3']

    def test_single_value(self):
        assert list(pat.RangeIter('int', '5-5')) == ['5']

    def test_descending_range(self):
        assert list(pat.RangeIter('int', '3-1')) == ['3', '2', '1']

    def test_size_property(self):
        assert len(pat.RangeIter('int', '0-9')) == 10

    def test_zero_to_zero_size_one(self):
        ri = pat.RangeIter('int', '0-0')
        assert len(ri) == 1
        assert list(ri) == ['0']

    def test_negative_start(self):
        assert list(pat.RangeIter('int', '-2-0')) == ['-2', '-1', '0']

    def test_values_are_strings(self):
        for v in pat.RangeIter('int', '1-5'):
            assert isinstance(v, str)

    def test_iterable_twice(self):
        ri = pat.RangeIter('int', '1-3')
        assert list(ri) == list(ri)

    def test_size_100(self):
        assert len(pat.RangeIter('int', '0-99')) == 100


# ---------------------------------------------------------------------------
# RangeIter -- hex type
# ---------------------------------------------------------------------------

class TestRangeIterHex:
    def test_hex_prefix_range(self):
        assert list(pat.RangeIter('hex', '0x00-0x03')) == ['00', '01', '02', '03']

    def test_hex_without_prefix(self):
        assert list(pat.RangeIter('hex', '0-3')) == ['00', '01', '02', '03']

    def test_hex_crosses_byte_boundary(self):
        assert list(pat.RangeIter('hex', '0x0f-0x11')) == ['0f', '10', '11']

    def test_hex_full_byte_size(self):
        assert len(pat.RangeIter('hex', '0x00-0xff')) == 256

    def test_hex_descending(self):
        assert list(pat.RangeIter('hex', '0x03-0x01')) == ['03', '02', '01']

    def test_hex_values_always_even_length(self):
        for v in pat.RangeIter('hex', '0-15'):
            assert len(v) % 2 == 0

    def test_hex_zero(self):
        assert list(pat.RangeIter('hex', '0-0')) == ['00']


# ---------------------------------------------------------------------------
# RangeIter -- float type
# ---------------------------------------------------------------------------

class TestRangeIterFloat:
    def test_float_basic_range(self):
        result = list(pat.RangeIter('float', '1.0-1.2'))
        assert result == ['1.0', '1.1', '1.2']

    def test_float_size(self):
        assert len(pat.RangeIter('float', '0.0-0.9')) == 10

    def test_float_two_decimal_places(self):
        assert list(pat.RangeIter('float', '0.00-0.02')) == ['0.00', '0.01', '0.02']

    def test_float_descending(self):
        result = list(pat.RangeIter('float', '1.2-1.0'))
        assert result[0] == '1.2'
        assert result[-1] == '1.0'

    def test_float_values_are_strings(self):
        for v in pat.RangeIter('float', '0.0-0.2'):
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# RangeIter -- letter types (lower / lowercase / upper / uppercase / letters)
# ---------------------------------------------------------------------------

class TestRangeIterLetters:
    def test_lowercase_single_chars(self):
        assert list(pat.RangeIter('lower', 'a-e')) == ['a', 'b', 'c', 'd', 'e']

    def test_uppercase_single_chars(self):
        assert list(pat.RangeIter('upper', 'A-E')) == ['A', 'B', 'C', 'D', 'E']

    def test_lowercase_alias_equals_lower(self):
        assert list(pat.RangeIter('lower', 'a-c')) == list(pat.RangeIter('lowercase', 'a-c'))

    def test_uppercase_alias_equals_upper(self):
        assert list(pat.RangeIter('upper', 'A-C')) == list(pat.RangeIter('uppercase', 'A-C'))

    def test_full_lowercase_alphabet_size(self):
        assert len(pat.RangeIter('lower', 'a-z')) == 26

    def test_full_uppercase_alphabet_size(self):
        assert len(pat.RangeIter('upper', 'A-Z')) == 26

    def test_letters_type_includes_lower(self):
        result = list(pat.RangeIter('letters', 'a-c'))
        for ch in ('a', 'b', 'c'):
            assert ch in result

    def test_multi_char_range_wraps(self):
        # 'z'->'aa'->'ab' = 3 elements
        result = list(pat.RangeIter('lower', 'z-ab'))
        assert result == ['z', 'aa', 'ab']
        assert len(result) == 3

    def test_letter_values_are_strings(self):
        for v in pat.RangeIter('lower', 'a-c'):
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# RangeIter -- error handling and random mode
# ---------------------------------------------------------------------------

class TestRangeIterEdgeCases:
    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match='Incorrect range type'):
            pat.RangeIter('invalid', '1-10')

    def test_invalid_int_format_raises(self):
        with pytest.raises(ValueError, match='Unsupported range'):
            pat.RangeIter('int', 'abc')

    def test_invalid_hex_format_raises(self):
        with pytest.raises(ValueError, match='Unsupported range'):
            pat.RangeIter('hex', 'xyz')

    def test_random_mode_size_is_maxint(self):
        import sys
        import random as rnd
        ri = pat.RangeIter('int', '0-100', random=rnd)
        assert len(ri) == sys.maxsize

    def test_random_int_values_in_range(self):
        import random as rnd
        ri = pat.RangeIter('int', '0-100', random=rnd)
        # random mode is infinite; sample via next(iter(...)) to avoid exhausting it
        values = [next(iter(ri)) for _ in range(10)]
        for v in values:
            assert 0 <= int(v) <= 100

    def test_random_hex_fmt_is_callable(self):
        # padhex is a callable; random_generator for hex uses fmt % int which
        # breaks on callables -- this documents the known patator limitation.
        import random as rnd
        ri = pat.RangeIter('hex', '0x00-0xff', random=rnd)
        with pytest.raises(TypeError):
            next(iter(ri))


# ---------------------------------------------------------------------------
# FileIter
# ---------------------------------------------------------------------------

class TestFileIter:
    def test_iterates_lines(self, tmp_path):
        f = tmp_path / 'words.txt'
        f.write_bytes(b'line1\nline2\nline3\n')
        fi = pat.FileIter(str(f))
        lines = list(fi)
        assert b'line1\n' in lines
        assert b'line3\n' in lines

    def test_can_iterate_multiple_times(self, tmp_path):
        f = tmp_path / 'words.txt'
        f.write_bytes(b'a\nb\n')
        fi = pat.FileIter(str(f))
        assert list(fi) == list(fi)

    def test_binary_content_preserved(self, tmp_path):
        f = tmp_path / 'binary.dat'
        f.write_bytes(b'\xde\xad\xbe\xef\n')
        lines = list(pat.FileIter(str(f)))
        assert b'\xde\xad\xbe\xef\n' in lines

    def test_filename_attribute_stored(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_bytes(b'')
        fi = pat.FileIter(str(f))
        assert fi.filename == str(f)


# ---------------------------------------------------------------------------
# count_lines()
# ---------------------------------------------------------------------------

class TestCountLines:
    def test_empty_file(self, tmp_path):
        f = tmp_path / 'empty.txt'
        f.write_bytes(b'')
        assert pat.count_lines(str(f)) == 0

    def test_three_terminated_lines(self, tmp_path):
        f = tmp_path / 'lines.txt'
        f.write_bytes(b'a\nb\nc\n')
        assert pat.count_lines(str(f)) == 3

    def test_no_trailing_newline_counts_only_interior(self, tmp_path):
        f = tmp_path / 'no_tail.txt'
        f.write_bytes(b'a\nb')
        assert pat.count_lines(str(f)) == 1

    def test_only_newlines(self, tmp_path):
        f = tmp_path / 'blank.txt'
        f.write_bytes(b'\n\n\n')
        assert pat.count_lines(str(f)) == 3


# ---------------------------------------------------------------------------
# Timing context manager
# ---------------------------------------------------------------------------

class TestTiming:
    def test_records_elapsed_time(self):
        with pat.Timing() as t:
            time_module.sleep(0.02)
        assert t.time >= 0.015

    def test_time_non_negative_on_immediate_exit(self):
        with pat.Timing() as t:
            pass
        assert t.time >= 0

    def test_time_attribute_present_after_exit(self):
        t = pat.Timing()
        with t:
            pass
        assert hasattr(t, 'time')

    def test_successive_timings_independent(self):
        with pat.Timing() as t1:
            pass
        with pat.Timing() as t2:
            time_module.sleep(0.01)
        assert t2.time >= t1.time


# ---------------------------------------------------------------------------
# match_range() standalone function
# ---------------------------------------------------------------------------

class TestMatchRange:
    def test_exact_match_true(self):
        assert pat.match_range(100, '100') is True

    def test_exact_match_false(self):
        assert pat.match_range(100, '200') is False

    def test_range_lower_bound_included(self):
        assert pat.match_range(10, '10-100') is True

    def test_range_upper_bound_included(self):
        assert pat.match_range(100, '10-100') is True

    def test_range_midpoint_included(self):
        assert pat.match_range(50, '10-100') is True

    def test_below_range_excluded(self):
        assert pat.match_range(5, '10-100') is False

    def test_above_range_excluded(self):
        assert pat.match_range(101, '10-100') is False

    def test_open_max_bound_lte(self):
        # '-100' means size <= 100
        assert pat.match_range(50, '-100') is True
        assert pat.match_range(100, '-100') is True
        assert pat.match_range(101, '-100') is False

    def test_open_min_bound_gte(self):
        # '100-' means size >= 100
        assert pat.match_range(100, '100-') is True
        assert pat.match_range(200, '100-') is True
        assert pat.match_range(99, '100-') is False

    def test_empty_range_raises(self):
        with pytest.raises(ValueError, match='Invalid interval'):
            pat.match_range(10, '-')

    def test_inverted_range_raises(self):
        with pytest.raises(ValueError, match='Invalid interval'):
            pat.match_range(10, '100-50')

    def test_float_size_in_range(self):
        assert pat.match_range(1.5, '1.0-2.0') is True

    def test_float_size_outside_range(self):
        assert pat.match_range(0.5, '1.0-2.0') is False

    def test_zero_exact(self):
        assert pat.match_range(0, '0') is True


# ---------------------------------------------------------------------------
# Response_Base
# ---------------------------------------------------------------------------

class TestResponseBase:
    def _r(self, code='200', mesg='OK', time=0.5, trace=None):
        return pat.Response_Base(code, mesg, time, trace)

    def test_code_stored(self):
        assert self._r(code='404').code == '404'

    def test_mesg_stored(self):
        assert self._r(mesg='Not Found').mesg == 'Not Found'

    def test_time_stored_from_float(self):
        assert self._r(time=1.23).time == 1.23

    def test_time_stored_from_timing_object(self):
        t = pat.Timing()
        t.time = 0.777
        resp = pat.Response_Base('0', 'msg', t)
        assert resp.time == 0.777

    def test_size_is_len_of_mesg(self):
        assert self._r(mesg='hello').size == 5

    def test_empty_mesg_size_zero(self):
        assert self._r(mesg='').size == 0

    def test_str_returns_mesg(self):
        assert str(self._r(mesg='hello world')) == 'hello world'

    def test_indicators_returns_three_values(self):
        code, size, time_str = self._r(code='200', mesg='hello', time=0.5).indicators()
        assert code == '200'
        assert size == 5
        assert '0.500' in time_str

    def test_indicators_time_three_decimal_places(self):
        _, _, time_str = self._r(time=1.0).indicators()
        assert time_str == '1.000'

    def test_match_code_exact_match(self):
        assert self._r(code='200').match_code('200')

    def test_match_code_exact_no_match(self):
        assert not self._r(code='200').match_code('404')

    def test_match_code_regex_dot_wildcard(self):
        assert self._r(code='200').match_code('2..')

    def test_match_code_regex_char_class(self):
        assert self._r(code='200').match_code('20[0-9]')

    def test_match_code_anchored_rejects_prefix(self):
        # '20$' should not match '200'
        assert not self._r(code='200').match_code('20')

    def test_match_size_exact(self):
        r = self._r(mesg='hello')  # size=5
        assert r.match_size('5')
        assert not r.match_size('4')

    def test_match_size_range_in(self):
        assert self._r(mesg='hello').match_size('1-10')

    def test_match_size_range_out(self):
        assert not self._r(mesg='hello').match_size('10-20')

    def test_match_time_range_in(self):
        assert self._r(time=0.5).match_time('0.1-1.0')

    def test_match_time_range_out(self):
        assert not self._r(time=0.5).match_time('1.0-2.0')

    def test_match_mesg_exact(self):
        assert self._r(mesg='Login incorrect.').match_mesg('Login incorrect.')
        assert not self._r(mesg='Login incorrect.').match_mesg('Login correct.')

    def test_match_mesg_no_partial(self):
        assert not self._r(mesg='Login incorrect.').match_mesg('Login')

    def test_match_fgrep_substring(self):
        r = self._r(mesg='bad password entered')
        assert r.match_fgrep('bad password')
        assert not r.match_fgrep('good password')

    def test_match_fgrep_case_sensitive(self):
        r = self._r(mesg='Hello World')
        assert r.match_fgrep('Hello')
        assert not r.match_fgrep('hello')

    def test_match_egrep_pattern_matches(self):
        assert self._r(mesg='Error 404').match_egrep(r'Error \d+')

    def test_match_egrep_pattern_no_match(self):
        assert not self._r(mesg='Error 404').match_egrep(r'Success \d+')

    def test_match_dispatches_by_key(self):
        r = self._r(code='200', mesg='test string')
        assert r.match('code', '200')
        assert r.match('fgrep', 'test')
        assert not r.match('code', '404')

    def test_dump_returns_bytes(self):
        assert isinstance(self._r().dump(), bytes)

    def test_dump_uses_trace_when_set(self):
        assert self._r(trace=b'trace bytes').dump() == b'trace bytes'

    def test_dump_falls_back_to_mesg(self):
        assert self._r(mesg='fallback', trace=None).dump() == b'fallback'

    def test_str_target_empty(self):
        assert self._r().str_target() == ''

    def test_available_conditions_complete(self):
        keys = {k for k, _ in pat.Response_Base.available_conditions}
        assert keys == {'code', 'size', 'time', 'mesg', 'fgrep', 'egrep'}

    def test_indicatorsfmt_three_columns(self):
        assert len(pat.Response_Base.indicatorsfmt) == 3

    def test_large_mesg_size_accurate(self):
        big = 'x' * 10000
        assert pat.Response_Base('0', big).size == 10000


# ---------------------------------------------------------------------------
# Response_HTTP
# ---------------------------------------------------------------------------

class TestResponseHTTP:
    def test_available_conditions_include_clen(self):
        keys = [k for k, _ in pat.Response_HTTP.available_conditions]
        assert 'clen' in keys

    def test_inherits_all_base_conditions(self):
        keys = [k for k, _ in pat.Response_HTTP.available_conditions]
        for k in ('code', 'size', 'time', 'mesg', 'fgrep', 'egrep'):
            assert k in keys

    def test_indicators_includes_content_length(self):
        resp = pat.Response_HTTP('200', 'body', 0.1, content_length=42)
        _, size_clen, _ = resp.indicators()
        assert '42' in size_clen

    def test_content_length_default_minus_one(self):
        assert pat.Response_HTTP('200', 'body').content_length == -1

    def test_str_returns_last_http_status_line(self):
        raw = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nbody'
        resp = pat.Response_HTTP('200', raw)
        assert 'HTTP/1.1 200 OK' in str(resp)

    def test_indicatorsfmt_has_three_columns(self):
        assert len(pat.Response_HTTP.indicatorsfmt) == 3


# ---------------------------------------------------------------------------
# MsgFilter
# ---------------------------------------------------------------------------

class TestMsgFilter:
    def test_non_empty_message_filtered_out(self):
        f = pat.MsgFilter()
        record = logging.LogRecord('test', logging.INFO, '', 0, 'some msg', None, None)
        assert f.filter(record) == 0

    def test_none_message_passes(self):
        f = pat.MsgFilter()
        record = logging.LogRecord('test', logging.INFO, '', 0, None, None, None)
        assert f.filter(record) == 1

    def test_empty_string_message_passes(self):
        f = pat.MsgFilter()
        record = logging.LogRecord('test', logging.INFO, '', 0, '', None, None)
        assert f.filter(record) == 1


# ---------------------------------------------------------------------------
# TCP_Connection and TCP_Cache
# ---------------------------------------------------------------------------

class TestTCPConnection:
    def test_fp_and_banner_stored(self):
        mock_fp = MagicMock()
        conn = pat.TCP_Connection(mock_fp, banner='220 FTP')
        assert conn.fp is mock_fp
        assert conn.banner == '220 FTP'

    def test_close_delegates_to_fp(self):
        mock_fp = MagicMock()
        pat.TCP_Connection(mock_fp).close()
        mock_fp.close.assert_called_once()

    def test_banner_defaults_to_none(self):
        assert pat.TCP_Connection(MagicMock()).banner is None


class TestTCPCache:
    @pytest.fixture(autouse=True)
    def _mock_logger(self):
        with patch('patator.patator.logger', create=True):
            yield

    def _cache_factory(self, conn, counter=None):
        class MockCache(pat.TCP_Cache):
            def connect(self, host, port, *args, **kwargs):
                if counter is not None:
                    counter[0] += 1
                return conn
        return MockCache()

    def _conn(self, banner='banner'):
        c = MagicMock(spec=pat.TCP_Connection)
        c.fp = MagicMock()
        c.banner = banner
        return c

    def test_bind_returns_fp_and_banner(self):
        conn = self._conn('Hello')
        fp, banner = self._cache_factory(conn).bind('127.0.0.1', 22, 'user')
        assert fp is conn.fp
        assert banner == 'Hello'

    def test_bind_same_key_reuses_connection(self):
        counter = [0]
        cache = self._cache_factory(self._conn(), counter)
        cache.bind('127.0.0.1', 22, 'user')
        cache.bind('127.0.0.1', 22, 'user')
        assert counter[0] == 1

    def test_bind_different_key_reconnects(self):
        counter = [0]
        cache = self._cache_factory(self._conn(), counter)
        cache.bind('127.0.0.1', 22, 'user1')
        cache.bind('127.0.0.1', 22, 'user2')
        assert counter[0] == 2

    def test_bind_different_host_separate_connections(self):
        counter = [0]
        cache = self._cache_factory(self._conn(), counter)
        cache.bind('10.0.0.1', 22, 'user')
        cache.bind('10.0.0.2', 22, 'user')
        assert counter[0] == 2

    def test_reset_forces_reconnect(self):
        counter = [0]
        cache = self._cache_factory(self._conn(), counter)
        cache.bind('127.0.0.1', 22, 'user')
        cache.reset()
        cache.bind('127.0.0.1', 22, 'user')
        assert counter[0] == 2

    def test_reset_with_no_current_is_noop(self):
        cache = object.__new__(pat.TCP_Cache)
        cache.cache = {}
        cache.curr = None
        cache.reset()  # must not raise

    def test_available_actions_has_reset(self):
        assert any(k == 'reset' for k, _ in pat.TCP_Cache.available_actions)

    def test_available_options_has_persistent(self):
        assert any(k == 'persistent' for k, _ in pat.TCP_Cache.available_options)


# ---------------------------------------------------------------------------
# Controller -- keyword-finder regex helpers
# ---------------------------------------------------------------------------

class TestControllerKeyFinders:
    def setup_method(self):
        self.ctrl = object.__new__(pat.Controller)

    def test_find_file_keys_basic(self):
        assert list(self.ctrl.find_file_keys('pass=FILE0')) == [0]

    def test_find_file_keys_multiple(self):
        keys = list(self.ctrl.find_file_keys('user=FILE0 pass=FILE1'))
        assert 0 in keys and 1 in keys

    def test_find_file_keys_absent(self):
        assert list(self.ctrl.find_file_keys('host=10.0.0.1')) == []

    def test_find_net_keys_basic(self):
        assert list(self.ctrl.find_net_keys('host=NET0')) == [0]

    def test_find_net_keys_absent(self):
        assert list(self.ctrl.find_net_keys('host=static')) == []

    def test_find_combo_keys_one_field(self):
        assert len(list(self.ctrl.find_combo_keys('user=COMBO10'))) == 1

    def test_find_combo_keys_two_fields(self):
        assert len(list(self.ctrl.find_combo_keys('user=COMBO10 pass=COMBO11'))) == 2

    def test_find_module_keys_basic(self):
        assert list(self.ctrl.find_module_keys('name=MOD0')) == [0]

    def test_find_module_keys_absent(self):
        assert list(self.ctrl.find_module_keys('name=TLD')) == []

    def test_find_range_keys_basic(self):
        assert list(self.ctrl.find_range_keys('data=RANGE0')) == [0]

    def test_find_range_keys_absent(self):
        assert list(self.ctrl.find_range_keys('data=FILE0')) == []

    def test_find_prog_keys_basic(self):
        assert list(self.ctrl.find_prog_keys('data=PROG0')) == [0]

    def test_find_prog_keys_absent(self):
        assert list(self.ctrl.find_prog_keys('data=static')) == []

    def test_expand_key_simple_pair(self):
        # expand_key yields lists (from str.split), not tuples
        assert list(self.ctrl.expand_key('host=10.0.0.1')) == [['host', '10.0.0.1']]

    def test_expand_key_splits_on_first_equals_only(self):
        result = list(self.ctrl.expand_key('url=http://x.com?a=1'))
        assert result == [['url', 'http://x.com?a=1']]


# ---------------------------------------------------------------------------
# Controller -- should_skip / should_free
# ---------------------------------------------------------------------------

class TestControllerShouldSkipFree:
    def setup_method(self):
        self.ctrl = object.__new__(pat.Controller)
        self.ctrl.ns = MagicMock()
        self.ctrl.ns.skip_list = []
        self.ctrl.ns.free_list = []

    def test_skip_empty_list_false(self):
        assert not self.ctrl.should_skip(['h1', 'u1'])

    def test_skip_single_condition_match(self):
        self.ctrl.ns.skip_list = [[(0, 'h1')]]
        assert self.ctrl.should_skip(['h1', 'u1'])

    def test_skip_single_condition_no_match(self):
        self.ctrl.ns.skip_list = [[(0, 'other')]]
        assert not self.ctrl.should_skip(['h1', 'u1'])

    def test_skip_multi_condition_all_match(self):
        self.ctrl.ns.skip_list = [[(0, 'h1'), (1, 'u1')]]
        assert self.ctrl.should_skip(['h1', 'u1'])

    def test_skip_multi_condition_partial_no_match(self):
        self.ctrl.ns.skip_list = [[(0, 'h1'), (1, 'other')]]
        assert not self.ctrl.should_skip(['h1', 'u1'])

    def test_skip_multiple_entries_any_match(self):
        self.ctrl.ns.skip_list = [[(0, 'other')], [(0, 'h1')]]
        assert self.ctrl.should_skip(['h1'])

    def test_free_empty_list_false(self):
        assert not self.ctrl.should_free({'host': '10.0.0.1'})

    def test_free_single_key_match(self):
        self.ctrl.ns.free_list = [[('host', '10.0.0.1')]]
        assert self.ctrl.should_free({'host': '10.0.0.1', 'user': 'admin'})

    def test_free_single_key_no_match(self):
        self.ctrl.ns.free_list = [[('host', '10.0.0.2')]]
        assert not self.ctrl.should_free({'host': '10.0.0.1'})

    def test_free_multi_key_all_match(self):
        self.ctrl.ns.free_list = [[('host', '10.0.0.1'), ('user', 'admin')]]
        assert self.ctrl.should_free({'host': '10.0.0.1', 'user': 'admin'})

    def test_free_multi_key_partial_no_match(self):
        self.ctrl.ns.free_list = [[('host', '10.0.0.1'), ('user', 'other')]]
        assert not self.ctrl.should_free({'host': '10.0.0.1', 'user': 'admin'})


# ---------------------------------------------------------------------------
# Controller -- lookup_actions
# ---------------------------------------------------------------------------

class TestControllerLookupActions:
    def setup_method(self):
        self.ctrl = object.__new__(pat.Controller)
        self.ctrl.ns = MagicMock()
        self.ctrl.ns.actions = {}

    def test_no_actions_returns_empty(self):
        assert self.ctrl.lookup_actions(pat.Response_Base('200', 'OK')) == {}

    def test_matching_code_returns_action(self):
        self.ctrl.ns.actions = {'ignore': [([('code', '200')], None)]}
        assert 'ignore' in self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))

    def test_non_matching_code_omits_action(self):
        self.ctrl.ns.actions = {'ignore': [([('code', '404')], None)]}
        assert 'ignore' not in self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))

    def test_negated_key_inverts_match(self):
        # 'code!' = only act when code does NOT match
        self.ctrl.ns.actions = {'ignore': [([('code!', '404')], None)]}
        assert 'ignore' in self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))

    def test_negated_key_excludes_when_matches(self):
        self.ctrl.ns.actions = {'ignore': [([('code!', '200')], None)]}
        assert 'ignore' not in self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))

    def test_all_conditions_must_match(self):
        self.ctrl.ns.actions = {'ignore': [([('code', '200'), ('fgrep', 'not found')], None)]}
        resp = pat.Response_Base('200', 'not found here')
        assert 'ignore' in self.ctrl.lookup_actions(resp)

    def test_partial_condition_fail_omits_action(self):
        self.ctrl.ns.actions = {'ignore': [([('code', '200'), ('fgrep', 'success')], None)]}
        assert 'ignore' not in self.ctrl.lookup_actions(pat.Response_Base('200', 'not found'))

    def test_action_opts_returned(self):
        self.ctrl.ns.actions = {'skip': [([('code', '200')], '0')]}
        assert self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))['skip'] == '0'

    def test_multiple_actions_matched(self):
        self.ctrl.ns.actions = {
            'ignore': [([('code', '200')], None)],
            'retry':  [([('code', '200')], None)],
        }
        actions = self.ctrl.lookup_actions(pat.Response_Base('200', 'OK'))
        assert 'ignore' in actions and 'retry' in actions

    def test_fgrep_condition_works(self):
        self.ctrl.ns.actions = {'ignore': [([('fgrep', 'fail')], None)]}
        assert 'ignore' in self.ctrl.lookup_actions(pat.Response_Base('0', 'auth fail'))

    def test_egrep_condition_works(self):
        self.ctrl.ns.actions = {'ignore': [([('egrep', r'err\d+')], None)]}
        assert 'ignore' in self.ctrl.lookup_actions(pat.Response_Base('0', 'err404'))


# ---------------------------------------------------------------------------
# Controller -- update_actions
# ---------------------------------------------------------------------------

class TestControllerUpdateActions:
    def setup_method(self):
        self.ctrl = object.__new__(pat.Controller)
        self.ctrl.ns = MagicMock()
        self.ctrl.ns.actions = {}
        self.ctrl.available_actions = ['ignore', 'retry', 'skip', 'free', 'quit', 'reset']
        self.ctrl.condition_delim = ','

    def test_basic_action_added(self):
        self.ctrl.update_actions('ignore:code=200')
        assert 'ignore' in self.ctrl.ns.actions

    def test_condition_parsed(self):
        self.ctrl.update_actions('ignore:code=200')
        conds, _ = self.ctrl.ns.actions['ignore'][0]
        assert ['code', '200'] in conds

    def test_multiple_comma_conditions(self):
        self.ctrl.update_actions('ignore:code=200,fgrep=OK')
        conds, _ = self.ctrl.ns.actions['ignore'][0]
        assert len(conds) == 2

    def test_comma_separated_actions(self):
        self.ctrl.update_actions('ignore,reset:code=500')
        assert 'ignore' in self.ctrl.ns.actions
        assert 'reset' in self.ctrl.ns.actions

    def test_action_equals_syntax_for_opts(self):
        self.ctrl.update_actions('skip=0:code=200')
        _, opts = self.ctrl.ns.actions['skip'][0]
        assert opts == '0'

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError, match='Unsupported action'):
            self.ctrl.update_actions('bogus_action:code=200')

    def test_multiple_calls_accumulate(self):
        self.ctrl.update_actions('ignore:code=200')
        self.ctrl.update_actions('ignore:code=404')
        assert len(self.ctrl.ns.actions['ignore']) == 2


# ---------------------------------------------------------------------------
# Controller -- register_skip / register_free
# ---------------------------------------------------------------------------

class TestControllerRegisterSkipFree:
    @pytest.fixture(autouse=True)
    def _mock_logger(self):
        with patch('patator.patator.logger', create=True):
            yield

    def setup_method(self):
        self.ctrl = object.__new__(pat.Controller)
        self.ctrl.ns = MagicMock()
        self.ctrl.ns.skip_list = []
        self.ctrl.ns.free_list = []

    def test_register_skip_appends_entry(self):
        self.ctrl.register_skip(['h1', 'u1'], '0')
        assert len(self.ctrl.ns.skip_list) == 1

    def test_register_skip_entry_contains_index_value(self):
        self.ctrl.register_skip(['h1', 'u1'], '0')
        assert (0, 'h1') in self.ctrl.ns.skip_list[0]

    def test_register_skip_multiple_indices(self):
        self.ctrl.register_skip(['h1', 'u1'], '0+1')
        entry = self.ctrl.ns.skip_list[0]
        assert (0, 'h1') in entry and (1, 'u1') in entry

    def test_register_free_appends_entry(self):
        self.ctrl.register_free({'host': '10.0.0.1'}, 'host')
        assert len(self.ctrl.ns.free_list) == 1

    def test_register_free_entry_contains_key_value(self):
        self.ctrl.register_free({'host': '10.0.0.1', 'user': 'admin'}, 'host')
        assert ('host', '10.0.0.1') in self.ctrl.ns.free_list[0]

    def test_register_free_multiple_keys(self):
        self.ctrl.register_free({'host': '10.0.0.1', 'user': 'admin'}, 'host+user')
        entry = self.ctrl.ns.free_list[0]
        assert ('host', '10.0.0.1') in entry and ('user', 'admin') in entry


# ---------------------------------------------------------------------------
# Controller -- available_encodings
# ---------------------------------------------------------------------------

class TestAvailableEncodings:
    def test_hex_encodes_to_hex_string(self):
        fn = pat.Controller.available_encodings['hex'][0]
        assert fn(b'A') == '41'

    def test_unhex_decodes_hex_string(self):
        fn = pat.Controller.available_encodings['unhex'][0]
        assert fn(b'41') == 'A'

    def test_hex_unhex_roundtrip(self):
        hex_fn = pat.Controller.available_encodings['hex'][0]
        unhex_fn = pat.Controller.available_encodings['unhex'][0]
        assert pat.b(unhex_fn(pat.b(hex_fn(b'hello')))) == b'hello'

    def test_b64_encodes_bytes(self):
        from base64 import b64encode
        fn = pat.Controller.available_encodings['b64'][0]
        assert fn(b'hello') == b64encode(b'hello').decode('ISO-8859-1')

    def test_md5_known_hash(self):
        fn = pat.Controller.available_encodings['md5'][0]
        assert fn(b'') == 'd41d8cd98f00b204e9800998ecf8427e'

    def test_sha1_known_hash(self):
        fn = pat.Controller.available_encodings['sha1'][0]
        assert fn(b'') == 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    def test_url_encodes_space_as_plus(self):
        fn = pat.Controller.available_encodings['url'][0]
        assert fn('hello world') == 'hello+world'

    def test_url_encodes_ampersand(self):
        fn = pat.Controller.available_encodings['url'][0]
        assert '&' not in fn('a&b')

    def test_exactly_six_encodings(self):
        assert set(pat.Controller.available_encodings) == {'hex', 'unhex', 'b64', 'md5', 'sha1', 'url'}

    def test_each_encoding_has_callable_and_description(self):
        for name, (fn, desc) in pat.Controller.available_encodings.items():
            assert callable(fn), f'{name}: function not callable'
            assert desc, f'{name}: empty description'


# ---------------------------------------------------------------------------
# Module list -- metadata completeness
# ---------------------------------------------------------------------------

class TestModuleList:
    def test_not_empty(self):
        assert len(pat.modules) > 0

    def test_names_are_unique(self):
        names = [n for n, _ in pat.modules]
        assert len(names) == len(set(names))

    def test_expected_modules_present(self):
        available = dict(pat.modules)
        for name in ('ftp_login', 'ssh_login', 'http_fuzz', 'dummy_test',
                     'dns_forward', 'dns_reverse', 'snmp_login', 'unzip_pass',
                     'smtp_login', 'pop_login', 'imap_login', 'smb_login',
                     'mysql_login', 'pgsql_login', 'vnc_login'):
            assert name in available, f'{name} not in modules'

    def test_dummy_test_uses_correct_class(self):
        assert dict(pat.modules)['dummy_test'][1] is pat.Dummy_test

    def test_each_module_has_response_class(self):
        for name, (_, cls) in pat.modules:
            assert hasattr(cls, 'Response'), f'{name} missing Response'

    def test_each_module_has_usage_hints(self):
        for name, (_, cls) in pat.modules:
            assert hasattr(cls, 'usage_hints'), f'{name} missing usage_hints'

    def test_each_module_has_available_options(self):
        for name, (_, cls) in pat.modules:
            assert hasattr(cls, 'available_options'), f'{name} missing available_options'

    def test_each_module_has_available_actions(self):
        for name, (_, cls) in pat.modules:
            assert hasattr(cls, 'available_actions'), f'{name} missing available_actions'

    def test_each_module_has_docstring(self):
        for name, (_, cls) in pat.modules:
            assert cls.__doc__, f'{name} missing docstring'


# ---------------------------------------------------------------------------
# Dummy_test module
# ---------------------------------------------------------------------------

class TestDummyTestModule:
    def setup_method(self):
        self.mod = pat.Dummy_test()

    def test_execute_returns_response_base(self):
        assert isinstance(self.mod.execute('data', delay='0'), pat.Response_Base)

    def test_execute_code_zero(self):
        assert self.mod.execute('data', delay='0').code == 0

    def test_execute_mesg_contains_data(self):
        assert 'hello' in str(self.mod.execute('hello', delay='0'))

    def test_execute_mesg_format(self):
        assert str(self.mod.execute('hello', data2='world', delay='0')) == 'hello / world'

    def test_execute_default_data2_empty(self):
        assert '/' in str(self.mod.execute('data', delay='0'))

    def test_execute_timing_non_negative(self):
        assert self.mod.execute('data', delay='0').time >= 0

    def test_available_keys_has_tst(self):
        assert 'TST' in pat.Dummy_test.available_keys

    def test_tst_key_returns_two_envs(self):
        elements, size = pat.Dummy_test.available_keys['TST']()
        assert size == 2
        assert set(elements) == {'prd', 'dev'}

    def test_response_class_is_response_base(self):
        assert pat.Dummy_test.Response is pat.Response_Base

    def test_available_options_has_data(self):
        assert any(k == 'data' for k, _ in pat.Dummy_test.available_options)


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

class TestProgress:
    def test_current_empty(self):
        assert pat.Progress().current == ''

    def test_done_count_zero(self):
        assert pat.Progress().done_count == 0

    def test_hits_count_zero(self):
        assert pat.Progress().hits_count == 0

    def test_skip_count_zero(self):
        assert pat.Progress().skip_count == 0

    def test_fail_count_zero(self):
        assert pat.Progress().fail_count == 0

    def test_seconds_25_elements(self):
        assert len(pat.Progress().seconds) == 25

    def test_seconds_all_nonzero_to_avoid_div_by_zero(self):
        assert all(s > 0 for s in pat.Progress().seconds)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

class TestModuleConstants:
    def test_version_is_1_1_0(self):
        assert pat.__version__ == '1.1.0'

    def test_banner_contains_patator(self):
        assert 'Patator' in pat.__banner__

    def test_banner_contains_version(self):
        assert '1.1.0' in pat.__banner__

    def test_banner_contains_python(self):
        assert 'Python' in pat.__banner__

    def test_dependencies_is_dict(self):
        assert isinstance(pat.dependencies, dict)

    def test_dependencies_has_expected_keys(self):
        for key in ('paramiko', 'dnspython', 'pycurl', 'impacket'):
            assert key in pat.dependencies

    def test_builtin_action_names(self):
        names = {k for k, _ in pat.Controller.builtin_actions}
        assert names == {'ignore', 'retry', 'skip', 'free', 'quit'}

    def test_builtin_action_descriptions_non_empty(self):
        for name, desc in pat.Controller.builtin_actions:
            assert desc, f'Builtin action {name!r} has empty description'


# ---------------------------------------------------------------------------
# expand_path()
# ---------------------------------------------------------------------------

class TestExpandPath:
    def test_tilde_expanded(self):
        result = pat.expand_path('~/test')
        assert not result.startswith('~')
        assert 'test' in result

    def test_env_var_expanded(self, monkeypatch):
        monkeypatch.setenv('PATATOR_TST', '/expanded/path')
        assert '/expanded/path' in pat.expand_path('$PATATOR_TST/file')

    def test_absolute_path_unchanged(self):
        assert pat.expand_path('/absolute/path') == '/absolute/path'


# ---------------------------------------------------------------------------
# on_windows()
# ---------------------------------------------------------------------------

class TestOnWindows:
    def test_returns_bool(self):
        assert isinstance(pat.on_windows(), bool)

    def test_matches_platform(self):
        assert pat.on_windows() == ('Win' in platform.system())


# ---------------------------------------------------------------------------
# strfutctime() / strflocaltime()
# ---------------------------------------------------------------------------

class TestStrftime:
    def test_utctime_format(self):
        assert re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', pat.strfutctime())

    def test_localtime_starts_with_date(self):
        assert re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', pat.strflocaltime())

    def test_both_return_strings(self):
        assert isinstance(pat.strfutctime(), str)
        assert isinstance(pat.strflocaltime(), str)


# ---------------------------------------------------------------------------
# TXTFormatter
# ---------------------------------------------------------------------------

class TestTXTFormatter:
    def _make_result_record(self, indicatorsfmt):
        """Build a log record that looks like a result row."""
        names = [n for n, _ in indicatorsfmt]
        extra = dict((n, 'val') for n in names)
        extra.update({'candidate': 'user:pass', 'num': '1', 'mesg': 'OK'})
        record = logging.LogRecord('patator', logging.INFO, '', 0, None, None, None)
        record.__dict__.update(extra)
        return record

    def test_formats_result_row(self):
        fmt = pat.TXTFormatter([('code', -5), ('size', -4), ('time', 7)])
        record = self._make_result_record([('code', -5), ('size', -4), ('time', 7)])
        output = fmt.format(record)
        assert 'val' in output

    def test_formats_regular_log_message(self):
        fmt = pat.TXTFormatter([('code', -5)])
        record = logging.LogRecord('patator', logging.INFO, '', 0, 'hello world', None, None)
        record.pname = 'Worker'
        output = fmt.format(record)
        assert 'hello world' in output

    def test_debug_level_includes_pname(self):
        fmt = pat.TXTFormatter([('code', -5)])
        record = logging.LogRecord('patator', logging.DEBUG, '', 0, 'dbg msg', None, None)
        record.pname = 'Producer'
        output = fmt.format(record)
        assert 'Producer' in output


# ---------------------------------------------------------------------------
# CSVFormatter
# ---------------------------------------------------------------------------

class TestCSVFormatter:
    def test_formats_result_as_csv(self):
        fmt = pat.CSVFormatter([('code', -5), ('size', -4)])
        extra = {'code': '200', 'size': '42', 'candidate': 'a:b', 'num': '1', 'mesg': 'OK'}
        record = logging.LogRecord('patator', logging.INFO, '', 0, None, None, None)
        record.__dict__.update(extra)
        output = fmt.format(record)
        assert '200' in output
        assert '42' in output

    def test_quotes_candidate_with_comma(self):
        fmt = pat.CSVFormatter([('code', -5)])
        extra = {'code': '200', 'candidate': 'user,pass', 'num': '1', 'mesg': 'OK'}
        record = logging.LogRecord('patator', logging.INFO, '', 0, None, None, None)
        record.__dict__.update(extra)
        output = fmt.format(record)
        assert '"user,pass"' in output


# ---------------------------------------------------------------------------
# XMLFormatter
# ---------------------------------------------------------------------------

class TestXMLFormatter:
    def test_formats_result_as_xml(self):
        fmt = pat.XMLFormatter([('code', -5)])
        extra = {
            'code': '200', 'candidate': 'user', 'num': '1',
            'mesg': 'OK', 'target': '',
        }
        record = logging.LogRecord('patator', logging.INFO, '', 0, None, None, None)
        record.__dict__.update(extra)
        output = fmt.format(record)
        assert '<result' in output
        assert '200' in output

    def test_escapes_xml_special_chars_in_mesg(self):
        fmt = pat.XMLFormatter([('code', -5)])
        extra = {
            'code': '0', 'candidate': 'a', 'num': '1',
            'mesg': '<script>alert(1)</script>', 'target': '',
        }
        record = logging.LogRecord('patator', logging.INFO, '', 0, None, None, None)
        record.__dict__.update(extra)
        output = fmt.format(record)
        assert '<script>' not in output
        assert '&lt;script&gt;' in output
