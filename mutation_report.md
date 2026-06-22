# Mutation Testing Report

Generated: 2026-06-22T07:01:02
Baseline tests pass: yes
Mutation limit: 60
Per-mutant timeout: 20s

## Summary

- Total mutants: 60
- Killed: 16
- Survived: 44
- Timed out (counted as killed): 0
- Mutation score: 26.67%

## Detailed Results

| # | Status | Line | Rule |
|---:|---|---:|---|
| 1 | KILLED | 66 | replace == -> != |
| 2 | KILLED | 70 | replace == -> != |
| 3 | SURVIVED | 148 | replace or -> and |
| 4 | SURVIVED | 149 | replace or -> and |
| 5 | SURVIVED | 159 | replace or -> and |
| 6 | SURVIVED | 160 | replace or -> and |
| 7 | SURVIVED | 172 | replace or -> and |
| 8 | SURVIVED | 173 | replace or -> and |
| 9 | SURVIVED | 187 | replace == -> != |
| 10 | SURVIVED | 191 | replace and -> or |
| 11 | SURVIVED | 209 | replace != -> == |
| 12 | SURVIVED | 223 | replace True -> False |
| 13 | SURVIVED | 227 | replace == -> != |
| 14 | SURVIVED | 228 | replace or -> and |
| 15 | SURVIVED | 233 | replace == -> != |
| 16 | SURVIVED | 239 | replace == -> != |
| 17 | SURVIVED | 246 | replace == -> != |
| 18 | SURVIVED | 251 | replace == -> != |
| 19 | SURVIVED | 260 | replace == -> != |
| 20 | SURVIVED | 265 | replace == -> != |
| 21 | SURVIVED | 322 | replace True -> False |
| 22 | SURVIVED | 324 | replace False -> True |
| 23 | SURVIVED | 373 | replace and -> or |
| 24 | SURVIVED | 376 | replace != -> == |
| 25 | SURVIVED | 392 | replace or -> and |
| 26 | SURVIVED | 403 | replace is not -> is |
| 27 | KILLED | 435 | replace <= -> < |
| 28 | KILLED | 461 | replace == -> != |
| 29 | SURVIVED | 505 | replace or -> and |
| 30 | KILLED | 517 | replace == -> != |
| 31 | KILLED | 519 | replace == -> != |
| 32 | KILLED | 522 | replace == -> != |
| 33 | KILLED | 531 | replace == -> != |
| 34 | KILLED | 542 | replace != -> == |
| 35 | KILLED | 555 | replace != -> == |
| 36 | KILLED | 560 | replace == -> != |
| 37 | KILLED | 563 | replace == -> != |
| 38 | SURVIVED | 574 | replace True -> False |
| 39 | KILLED | 582 | replace True -> False |
| 40 | SURVIVED | 644 | replace == -> != |
| 41 | KILLED | 689 | replace != -> == |
| 42 | KILLED | 694 | replace or -> and |
| 43 | SURVIVED | 753 | replace == -> != |
| 44 | SURVIVED | 797 | replace or -> and |
| 45 | SURVIVED | 808 | replace and -> or |
| 46 | SURVIVED | 814 | replace and -> or |
| 47 | SURVIVED | 819 | replace is -> is not |
| 48 | SURVIVED | 820 | replace is -> is not |
| 49 | SURVIVED | 821 | replace is -> is not |
| 50 | SURVIVED | 825 | replace is -> is not |
| 51 | SURVIVED | 826 | replace is -> is not |
| 52 | SURVIVED | 827 | replace is -> is not |
| 53 | SURVIVED | 828 | replace is -> is not |
| 54 | SURVIVED | 829 | replace is -> is not |
| 55 | SURVIVED | 832 | replace and -> or |
| 56 | SURVIVED | 891 | replace False -> True |
| 57 | SURVIVED | 892 | replace False -> True |
| 58 | SURVIVED | 899 | replace True -> False |
| 59 | SURVIVED | 952 | replace is -> is not |
| 60 | KILLED | 1039 | replace == -> != |

## Survived Mutants

1. Line 148 (replace or -> and)
   - Original:   if runtime_file or log_dir:
   - Mutated:    if runtime_file and log_dir:
2. Line 149 (replace or -> and)
   - Original:     runtime_log = os.path.join(log_dir or '', runtime_file or 'RUNTIME.log')
   - Mutated:      runtime_log = os.path.join(log_dir and '', runtime_file or 'RUNTIME.log')
3. Line 159 (replace or -> and)
   - Original:   if csv_file or log_dir:
   - Mutated:    if csv_file and log_dir:
4. Line 160 (replace or -> and)
   - Original:     results_csv = os.path.join(log_dir or '', csv_file or 'RESULTS.csv')
   - Mutated:      results_csv = os.path.join(log_dir and '', csv_file or 'RESULTS.csv')
5. Line 172 (replace or -> and)
   - Original:   if xml_file or log_dir:
   - Mutated:    if xml_file and log_dir:
6. Line 173 (replace or -> and)
   - Original:     results_xml = os.path.join(log_dir or '', xml_file or 'RESULTS.xml')
   - Mutated:      results_xml = os.path.join(log_dir and '', xml_file or 'RESULTS.xml')
7. Line 187 (replace == -> !=)
   - Original:           if arg[0] == '-':
   - Mutated:            if arg[0] != '-':
8. Line 191 (replace and -> or)
   - Original:               if not arg.startswith('--') and len(arg) > 2:
   - Mutated:                if not arg.startswith('--') or len(arg) > 2:
9. Line 209 (replace != -> ==)
   - Original:         if offset != -1:
   - Mutated:          if offset == -1:
10. Line 223 (replace True -> False)
   - Original:   while True:
   - Mutated:    while False:
11. Line 227 (replace == -> !=)
   - Original:     if action == 'quit':
   - Mutated:      if action != 'quit':
12. Line 228 (replace or -> and)
   - Original:       if xml_file or log_dir:
   - Mutated:        if xml_file and log_dir:
13. Line 233 (replace == -> !=)
   - Original:     elif action == 'headers':
   - Mutated:      elif action != 'headers':
14. Line 239 (replace == -> !=)
   - Original:     elif action == 'result':
   - Mutated:      elif action != 'result':
15. Line 246 (replace == -> !=)
   - Original:       if typ == 'fail':
   - Mutated:        if typ != 'fail':
16. Line 251 (replace == -> !=)
   - Original:     elif action == 'save_response':
   - Mutated:      elif action != 'save_response':
17. Line 260 (replace == -> !=)
   - Original:     elif action == 'save_hit':
   - Mutated:      elif action != 'save_hit':
18. Line 265 (replace == -> !=)
   - Original:     elif action == 'setLevel':
   - Mutated:      elif action != 'setLevel':
19. Line 322 (replace True -> False)
   - Original:   has_ipy = True
   - Mutated:    has_ipy = False
20. Line 324 (replace False -> True)
   - Original:   has_ipy = False
   - Mutated:    has_ipy = True
21. Line 373 (replace and -> or)
   - Original:     return os.path.exists(fpath) and os.access(fpath, os.X_OK)
   - Mutated:      return os.path.exists(fpath) or os.access(fpath, os.X_OK)
22. Line 376 (replace != -> ==)
   - Original:   if on_windows() and fname[-4:] != '.exe':
   - Mutated:    if on_windows() and fname[-4:] == '.exe':
23. Line 392 (replace or -> and)
   - Original:       return create_time_dir(opt_dir or '/tmp/patator', opt_auto)
   - Mutated:        return create_time_dir(opt_dir and '/tmp/patator', opt_auto)
24. Line 403 (replace is not -> is)
   - Original:       if assume_yes or input("Directory '%s' is not empty, do you want to wipe it ? [Y/n]: " % top_path) != 'n':
   - Mutated:        if assume_yes or input("Directory '%s' is empty, do you want to wipe it ? [Y/n]: " % top_path) != 'n':
25. Line 505 (replace or -> and)
   - Original:       m = re.match('(-?[^-]+)-(-?[^-]+)$', rng) # 5-50 or -5-50 or 5--50 or -5--50
   - Mutated:        m = re.match('(-?[^-]+)-(-?[^-]+)$', rng) # 5-50 and -5-50 or 5--50 or -5--50
26. Line 574 (replace True -> False)
   - Original:         while True:
   - Mutated:          while False:
27. Line 644 (replace == -> !=)
   - Original:   if signum == signal.SIGALRM:
   - Mutated:    if signum != signal.SIGALRM:
28. Line 753 (replace == -> !=)
   - Original:         if self.current_indent == 0 and heading == 'Options':
   - Mutated:          if self.current_indent != 0 and heading == 'Options':
29. Line 797 (replace or -> and)
   - Original:     tag        := any unique string (eg. T@G or _@@_ or ...)
   - Mutated:      tag        := any unique string (eg. T@G and _@@_ or ...)
30. Line 808 (replace and -> or)
   - Original: Please read the README inside for more examples and usage information.
   - Mutated:  Please read the README inside for more examples or usage information.
31. Line 814 (replace and -> or)
   - Original:     exe_grp.add_option('-x', dest='actions', action='append', default=[], metavar='arg', help='actions and conditions, see Syntax below')
   - Mutated:      exe_grp.add_option('-x', dest='actions', action='append', default=[], metavar='arg', help='actions or conditions, see Syntax below')
32. Line 819 (replace is -> is not)
   - Original:     exe_grp.add_option('-C', dest='combo_delim', default=':', metavar='str', help="delimiter string in combo files (default is ':')")
   - Mutated:      exe_grp.add_option('-C', dest='combo_delim', default=':', metavar='str', help="delimiter string in combo files (default is not ':')")
33. Line 820 (replace is -> is not)
   - Original:     exe_grp.add_option('-X', dest='condition_delim', default=',', metavar='str', help="delimiter string in conditions (default is ',')")
   - Mutated:      exe_grp.add_option('-X', dest='condition_delim', default=',', metavar='str', help="delimiter string in conditions (default is not ',')")
34. Line 821 (replace is -> is not)
   - Original:     exe_grp.add_option('--allow-ignore-failures', dest='allow_ignore_failures', action='store_true', help="failures cannot be ignored with -x (this is by design to avoid false negatives) this option overrides this safeguard")
   - Mutated:      exe_grp.add_option('--allow-ignore-failures', dest='allow_ignore_failures', action='store_true', help="failures cannot be ignored with -x (this is not by design to avoid false negatives) this option overrides this safeguard")
35. Line 825 (replace is -> is not)
   - Original:     opt_grp.add_option('--rate-limit', dest='rate_limit', type='float', default=0, metavar='N', help='wait N seconds between each attempt (default is 0)')
   - Mutated:      opt_grp.add_option('--rate-limit', dest='rate_limit', type='float', default=0, metavar='N', help='wait N seconds between each attempt (default is not 0)')
36. Line 826 (replace is -> is not)
   - Original:     opt_grp.add_option('--timeout', dest='timeout', type='int', default=0, metavar='N', help='wait N seconds for a response before retrying payload (default is 0)')
   - Mutated:      opt_grp.add_option('--timeout', dest='timeout', type='int', default=0, metavar='N', help='wait N seconds for a response before retrying payload (default is not 0)')
37. Line 827 (replace is -> is not)
   - Original:     opt_grp.add_option('--max-retries', dest='max_retries', type='int', default=4, metavar='N', help='skip payload after N retries (default is 4) (-1 for unlimited)')
   - Mutated:      opt_grp.add_option('--max-retries', dest='max_retries', type='int', default=4, metavar='N', help='skip payload after N retries (default is not 4) (-1 for unlimited)')
38. Line 828 (replace is -> is not)
   - Original:     opt_grp.add_option('-t', '--threads', dest='num_threads', type='int', default=10, metavar='N', help='number of threads (default is 10)')
   - Mutated:      opt_grp.add_option('-t', '--threads', dest='num_threads', type='int', default=10, metavar='N', help='number of threads (default is not 10)')
39. Line 829 (replace is -> is not)
   - Original:     opt_grp.add_option('--groups', dest='groups', default='', metavar='', help="default is to iterate over the cartesian product of all payload sets, use this option to iterate over sets simultaneously instead (aka pitchfork), see syntax inside (default is '0,1..n')")
   - Mutated:      opt_grp.add_option('--groups', dest='groups', default='', metavar='', help="default is not to iterate over the cartesian product of all payload sets, use this option to iterate over sets simultaneously instead (aka pitchfork), see syntax inside (default is '0,1..n')")
40. Line 832 (replace and -> or)
   - Original:     log_grp.add_option('-l', dest='log_dir', metavar='DIR', help="save output and response data into DIR ")
   - Mutated:      log_grp.add_option('-l', dest='log_dir', metavar='DIR', help="save output or response data into DIR ")
41. Line 891 (replace False -> True)
   - Original:     self.ns.paused = False
   - Mutated:      self.ns.paused = True
42. Line 892 (replace False -> True)
   - Original:     self.ns.quit_now = False
   - Mutated:      self.ns.quit_now = True
43. Line 899 (replace True -> False)
   - Original:     logsvc.daemon = True
   - Mutated:      logsvc.daemon = False
44. Line 952 (replace is -> is not)
   - Original:             print('IPy (https://github.com/haypo/python-ipy) is required for using NET keyword.')
   - Mutated:              print('IPy (https://github.com/haypo/python-ipy) is not required for using NET keyword.')

## Notes

- This is a mutation testing approach; it does not parse Python AST.
- Surviving mutants indicate potential test blind spots or equivalent mutants.
