---
name: binary-analysis-recovery
description: "Reverse engineer and analyze binary packages — Windows (PyInstaller EXEs, Mono/.NET) and Linux (.so shared objects via radare2). Covers EXE extraction, .pyc decompilation, source reconstruction, DLL→SO migration, and radare2 .so disassembly/decompilation workflow."
tags:
  - reverse-engineering
  - pyinstaller
  - decompilation
  - exe
  - binary
  - windows-to-linux
  - radare2
  - elf
  - shared-library
---

# Binary Analysis & Recovery

Reverse engineer Windows binary packages and Linux shared objects to recover source code, analyze architecture, and port across platforms.

## Scope

This skill covers two domains:
1. **Windows binaries** (PyInstaller EXEs, Mono/.NET): identify → extract → decompile → reconstruct → port
2. **Linux .so shared libraries** (via radare2): disassemble → decompile → trace symbols → analyze cross-references

---

# Part A: Windows Binary Recovery

## Workflow

### Phase 1: Identify the Binary

```bash
file app.exe
# PE32+ executable (GUI) x86-64, for MS Windows → PyInstaller candidate
```

PyInstaller EXEs contain:
- A CArchive/PKG section with compressed Python bytecode
- A PYZ section with standard library + third-party modules
- Embedded DLLs (.pyd, VCRUNTIME*.dll, python*.dll)

### Phase 2: Extract the Archive

```bash
# Step 1: Download pyinstxtractor
curl -sL -o pyinstxtractor.py \
  https://raw.githubusercontent.com/extremecoders-re/pyinstxtractor/master/pyinstxtractor.py

# Step 2: Extract
python3 pyinstxtractor.py app.exe
# → Creates app.exe_extracted/ directory
```

Output includes:
- `app_v1.pyc` — main entry point (in PKG/CArchive section)
- `PYZ-00.pyz` — compressed library archive (PyInstaller format, NOT a zip)
- `*.dll`, `*.pyd` — Windows-native runtime files

### Phase 3: Extract PYZ Modules

PyInstaller's `PYZ-00.pyz` is a proprietary compressed archive. Use `pyi-archive_viewer` (part of PyInstaller package):

```bash
pip install pyinstaller

# Interactive: List contents → Extract custom modules
pyi-archive_viewer app.exe_extracted/PYZ-00.pyz
# Commands inside viewer:
#   S          — list contents
#   X <name>   — extract named module (then prompts for output path)
#   Q          — quit
```

**⚠️ Critical: Interactive extraction format**

The `X` command is TWO-STEP, not inline. DO NOT use `X name /path/to/output` — that fails with "No entry named 'name /path' found". Use the interactive sequence:

```bash
X
asn_decode_api
/tmp/asn_decode_api.pyc
```

For automated extraction via pipe, use `printf` with each input on its own line:

```bash
printf 'X\nmodule_name\n/path/out.pyc\nQ\n' | pyi-archive_viewer PYZ-00.pyz
```

**Never** mix the module name and output path on the same line — the viewer reads them as separate inputs.

Custom modules to look for: the main app script, custom decode/encode modules, vendor-specific parsers. Ignore standard library modules (they're already available on the target Python). The PYZ listing shows typecode (0=compiled, 1=source) and size — focus on non-stdlib modules (e.g. `asn_decode_api`, `asn_spec`, vendor-specific modules).

### Phase 4: Decompile .pyc to Source

```bash
pip install uncompyle6

uncompyle6 app_v1.pyc > app_v1_decompiled.py
# Repeat for all custom .pyc from PYZ
```

**Pitfalls:**
- `uncompyle6` may fail with "Unknown magic number" if the .pyc is from a different Python version than the decompiler's runtime. The binary was compiled for the version shown by `pyinstxtractor` (e.g. "Python version: 3.7").
- Output may have syntax errors in edge cases — fix manually.
- The `asn1tools` or other third-party libs in PYZ don't need decompilation; just install the pip package instead.

### Phase 5: Reconstruct the Source Project

```bash
mkdir -p project_name/
# Copy decompiled source
cp app_v1_decompiled.py project_name/main.py
# Copy custom modules from PYZ extraction
cp extracted/asn_decode_api.py project_name/
cp extracted/asn_spec.py project_name/
# Install dependencies (skip what's in PYZ as standard lib)
pip install flask dpkt asn1tools mavenir_xml_decode  # etc.
```

### Phase 6: Fix Windows-isms

| Windows Artifact | Linux Fix |
|-----------------|-----------|
| `C:\\path\\` hardcoded paths | Use `os.path.join(BASE_DIR, ...)` |
| `python37.dll` | Use system Python 3.x |
| `.pyd` files (Python C extensions) | Built into Python interpreter, delete |
| `VCRUNTIME*.dll`, `api-ms-win-crt-*.dll` | Delete — Linux CRT handles these |
| `base_library.zip` | Delete — use system Python's stdlib |
| `PYZ-00.pyz` and `PYZ-00.pyz_extracted/` | Delete — conflicts with stdlib imports |

### Phase 7: Verify

```bash
# Test imports
python3 -c "from asn_spec import prepare_spec_info; print('OK')"

# Test decode path
python3 -c "
from asn_decode_api import decode_hi2_cs_message
result = decode_hi2_cs_message(b'\\xa1\\x03\\x02\\x01\\x00', 'hw_cs')
print(f'Decode OK: {len(result)} results')
"

# Start server and smoke test
curl -s http://localhost:5000/ | grep -c '<title>'
```

## Pitfalls (Windows)

### PYZ Conflicts with Standard Library

The `PYZ-00.pyz_extracted` directory contains **decompiled/stripped standard library files** (argparse.py, datetime.py, json/, logging/, etc.) that have invalid Python syntax. **Never add this directory to `sys.path`** — it will shadow the real standard library and cause `SyntaxError` on any import.

**DO:**
```python
# Copy only custom modules to a clean directory
cp PYZ-00.pyz_extracted/asn_decode_api.py .
cp PYZ-00.pyz_extracted/asn_spec.py .
```

**DON'T:**
```python
sys.path.insert(0, "PYZ-00.pyz_extracted")  # BREAKS stdlib imports
```

### ASN.1 File Paths in Decompiled Code

Decompiled code often has hardcoded Windows paths like:
```python
HI2Operations_hw = os.path.join(current_path, "asnfile", "HI2Operations_hw.asn")
```
Where `current_path = os.getcwd()`. This works on Linux if you `cd` to the right directory. Alternatively, override with:
```python
import asn_spec
asn_spec.current_path = "/path/to/asnfile"
```

### .pyc Magic Number Mismatch

`uncompyle6` running on Python 3.12 may fail to decompile Python 3.7 .pyc files. Workarounds:
- Use `pycdc` (C++ decompiler, more version-tolerant): `pip install pycdc`
- Accept partial decompilation and fix the rest manually
- The source from a different build (e.g., from the project's build directory) may be better quality than the PYZ's bytecode

---

# Part B: Linux .so Analysis with radare2

## Prerequisites

```bash
# Install radare2 (if not installed)
sudo apt install radare2 || pip install r2pipe

# Install r2dec plugin for C decompilation
r2pm -i r2dec
```

## Workflow

### 1. Open with Analysis

```bash
# Quick auto-analysis
r2 -A libexample.so

# Recommended: cache + full analysis
r2 -e bin.cache=true /path/to/lib.so
# Then inside r2:
aaa     # full analysis (functions, references, strings)
aap     # find function prologues
afl     # list all functions
```

### 2. Navigate Functions

```r2
# List functions
afl

# Go to a function
s 0x0002f58a              # use raw address, not debug symbol prefix
s sym.function_name       # or use symbol name

# View function info
afn sym.function_name     # function info
afvd                      # local variables
```

**⚠️ Navigation pitfall**: Always jump with the raw address `s 0xaddr`, never with `s dbg.sym_name`. The `pdf` and `pdc` commands may not recognize symbol names with the `dbg.` prefix.

### 3. Disassemble

```r2
pdf                       # print current function disassembly
pdf @ sym.function_name   # print specific function
pd 20                     # print 20 instructions from current offset
pd 20 @ 0xaddress         # print 20 instructions from address
```

### 4. Decompile to C (r2dec)

```r2
pdc                       # decompile current function to pseudo-C
pdc > func.c              # save to file
```

### 5. Symbols and Strings

```r2
is                        # symbol table
ii                        # imported symbols
ie                        # exported symbols
iS                        # section info
izz                       # all strings
iz                        # strings in current section
```

### 6. Cross-references

```r2
axt sym.function_name     # who calls this function
axf sym.function_name     # which functions this function calls
```

### 7. Save Analysis Output

```bash
# From within r2, or pipe:
afl > functions.txt
pdc > func.c
izz > strings.txt
```

## Quick-start Flow

```r2
# Full pipeline in one pass:
r2 -e bin.cache=true /path/to/lib.so
aaa
afl | grep keyword        # find your target function
s 0xaddr                  # jump to it
pdf                       # see assembly
pdc                       # see C code
izz | grep string         # find relevant strings
axt 0xaddr                # check callers
```

## Reference Files

- `references/pyinstaller-exe-extraction.md` — Detailed extraction steps with error handling
- `references/li-asn1-decoder-case-study.md` — Full case study of PyInstaller reverse engineering
- `references/radare2-commands.md` — radare2 .so analysis command quick reference

<!-- Note: Add session-specific detail files under references/ when a particular binary has unusual structure -->
