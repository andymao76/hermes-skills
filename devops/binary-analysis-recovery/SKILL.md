---
name: binary-analysis-recovery
description: "Reverse engineer and recover source code from Windows binary packages (PyInstaller EXEs, Mono/.NET assemblies, etc.) for Linux porting and analysis. Covers EXE extraction, .pyc decompilation, source reconstruction, and DLL→SO migration."
tags:
  - reverse-engineering
  - pyinstaller
  - decompilation
  - exe
  - binary
  - windows-to-linux
---

# Binary Analysis & Recovery

Reverse engineer Windows binary packages to recover source code, port to Linux, and analyze architecture.

## Scope

This skill covers the full pipeline: identify binary type → extract embedded payload → decompile/recover source → reconstruct build → clean up platform-specific artifacts.

Currently specialized for **PyInstaller-packaged Python EXEs** (the most common format for Python tools distributed as .exe).

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

```
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

## Pitfalls

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

## Reference Files

- `references/pyinstaller-exe-extraction.md` — Detailed extraction steps with error handling

<!-- Note: Add session-specific detail files under references/ when a particular EXE has unusual structure -->
