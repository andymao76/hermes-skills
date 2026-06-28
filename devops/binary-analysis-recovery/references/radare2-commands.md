# radare2 .so Analysis — Command Quick Reference

## Open & Analyze

| Command | Purpose |
|---------|---------|
| `r2 -A lib.so` | Auto-analyze on open |
| `r2 -e bin.cache=true lib.so` | Open with binary cache (recommended) |
| `aaa` | Full analysis: functions, references, strings |
| `aap` | Find function prologues |

## Function Analysis

| Command | Purpose |
|---------|---------|
| `aa` | Analyze all functions |
| `afl` | List all functions |
| `af` | Analyze current function |
| `afn sym` | Show function info |
| `afvd` | Show local variables |

## Navigation

| Command | Purpose |
|---------|---------|
| `s 0xaddr` | Jump to address (use raw hex, no `dbg.` prefix) |
| `s sym.func` | Jump to symbol |

## Disassembly

| Command | Purpose |
|---------|---------|
| `pdf` | Print current function disassembly |
| `pdf @ sym.func` | Print specific function |
| `pd N` | Print N instructions from here |
| `pd N @ 0xaddr` | Print N instructions from address |

## C Decompilation (r2dec)

| Command | Purpose |
|---------|---------|
| `pdc` | Decompile current function to C |
| `pdc > func.c` | Save to file |

## Symbols & Strings

| Command | Purpose |
|---------|---------|
| `is` | Symbol table |
| `ii` | Imported symbols |
| `ie` | Exported symbols |
| `iS` | Section info |
| `izz` | All strings in binary |
| `iz` | Strings in current section |

## Cross-references

| Command | Purpose |
|---------|---------|
| `axt sym.func` | Find callers of func |
| `axf sym.func` | Find func's callees |

## Debug (executable ELF only)

| Command | Purpose |
|---------|---------|
| `ood` | Open and run target |
| `dcu sym.main` | Continue until main |
| `db 0xaddr` | Set breakpoint |
| `dc` | Continue execution |
| `dr` | Show registers |

## Output to Files

```bash
afl > functions.txt
pdc > func.c
izz > strings.txt
is > symbols.txt
```

## ⚠️ Pitfalls

- **Navigation**: Always use raw address `s 0xaddr`. Do NOT use `s dbg.sym_name` — `pdf`/`pdc` may fail with `dbg.` prefix.
- **r2dec required**: `pdc` needs r2dec plugin installed via `r2pm -i r2dec`.
- **Cache**: Always use `-e bin.cache=true` on first open for large .so files to speed up subsequent analysis.
