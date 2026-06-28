---
name: elf-binary-analysis
description: "Analyze Linux ELF shared objects (.so files) and executables using radare2 — full workflow: open → function analysis → disassembly → C decompilation → cross-references → string/symbol inspection. Covers .so library reverse engineering for telecom LI systems."
tags:
  - reverse-engineering
  - radare2
  - elf
  - so
  - binary-analysis
  - disassembly
---

# ELF Binary Analysis with radare2

Analyze Linux ELF shared objects (`.so` files), executables, and object files using radare2. Common use case: reverse engineer telecom LI `lib*.so` libraries to understand X1/X2/X3 interface protocol implementations.

## Workflow

### Phase 1: Open the .so File

```bash
# Recommended: with binary cache + full analysis
r2 -e bin.cache=true /path/to/libexample.so

# Inside r2 shell, run full analysis:
aaa     # full analysis (functions, cross-references, strings)
aap     # find function preludes
afl     # list all functions (verify analysis worked)
```

Or open with `-A` for auto-analysis (slightly less control):
```bash
r2 -A libexample.so
```

### Phase 2: Navigate and Inspect Functions

```r2
# List all functions
afl

# Jump to a function by address (NOT by name with dbg. prefix)
s 0x0002f58a

# Show function info
afn
afvd                # local variables

# Disassembly
pdf                 # print current function disassembly
pd 20               # print 20 instructions from current offset
pd 20 @ 0xaddress   # print from specific address
```

**⚠️ Critical pitfall**: When jumping, use the bare function entry address, e.g. `s 0x0002f58a`. Do NOT use `s dbg.hwepc_x1_addTarget` — `pdf` and `pdc` may fail to recognize names with the `dbg.` prefix.

### Phase 3: Decompile to C

Requires the `r2dec` plugin:
```bash
r2pm -i r2dec
```

```r2
s 0x0002f58a     # jump to function entry
pdc              # decompile current function to pseudo-C
pdc > func.c     # save to file
```

### Phase 4: String and Symbol Analysis

```r2
izz              # full string table
iz               # strings in current section
is               # symbol table
iS               # section info
ii               # imported symbols
ie               # exported symbols
```

### Phase 5: Cross-Reference Analysis

```r2
axt sym.function_name    # find where this function is called FROM
axf sym.function_name    # find what this function calls INTO
axt 0xaddress            # cross-reference by address
```

### Phase 6: Save Results

```r2
afl > functions.txt
pdc > func.c
izz > strings.txt
is > symbols.txt
```

## Quick-Start Flow

```r2
r2 -e bin.cache=true /path/to/xxx.so
aaa       # full analysis
afl       # list functions
s 0xaddr  # jump to target function
pdf       # disassembly
pdc       # pseudo-C decompile
izz       # strings
is        # symbols
axt sym   # cross-references
```

## Common Commands Reference

| Command | Function |
|---------|----------|
| `aa` | Analyze all functions |
| `aaa` | Full analysis (functions, refs, strings) |
| `aap` | Find function preludes |
| `afl` | List all functions |
| `af` | Analyze current function |
| `afn` | Show function info |
| `afvd` | Show local variables |
| `pdf` | Print current function disassembly |
| `pd N` | Print N instructions |
| `pdc` | Decompile to C (r2dec plugin) |
| `izz` | Full string table |
| `iz` | Section strings |
| `is` | Symbol table |
| `iS` | Section info |
| `ii` | Imported symbols |
| `ie` | Exported symbols |
| `axt` | Find cross-references TO symbol |
| `axf` | Find what symbol calls |
| `s addr` | Seek to address |
| `db addr` | Set breakpoint |
| `dc` | Continue execution |
| `dr` | View registers |
| `ood` | Open and debug (for executables) |

## Pitfalls

### 1. Avoid `dbg.` prefix on symbol names
When seeking, always use the raw address `s 0xaddr`. Do NOT use `s dbg.sym_name` — `pdf`/`pdc` parsing may fail on prefixed names.

### 2. Analysis must be complete
If `afl` returns no or few functions, run `aaa` again. For heavily optimized/stripped binaries, use `aaa` instead of `aa` to ensure full coverage.

### 3. `pdc` requires r2dec
If `pdc` is not available, install with `r2pm -i r2dec`. Without it, fall back to manual disassembly with `pdf`.

### 4. .so files cannot be debugged
Dynamic analysis (breakpoints, step) only works on executables, not shared objects. For .so files, use `ood` only if the .so is loaded by a debuggable executable.

### 5. Endianness
Telecom .so files may be big-endian for certain architectures. Check with `iS` or `e cfg.bigendian = true` if needed.
