# SPDX-License-Identifier: MPL-2.0
"""Compile original preview research into an isolated ABC, never replace host classes.

Requires external FFDec 26.4.0, Java 17 and optional research-only JPype1 1.6.0.
The normal stdlib mod build does not import or require JPype. No installation,
launch, download or host source export is performed by this command.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path

from abc_index import ABC, abcs
from preview_module_source import provider_source

HOST_SHA256 = '7d24a5910b9a0b3dfdae21443e3f0b7edd2510d6269d8407b6d0d31a5178a317'
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_imports(sources, host_classes, own_classes):
    """FFDec permits unresolved names; do not treat compilation as resolution."""
    imports = {name for source in sources for name in
               re.findall(r'\bimport\s+([\w.]+)\s*;', source)}
    missing = sorted(name for name in imports if not name.startswith('flash.')
                     and name not in host_classes and name not in own_classes)
    if missing:
        raise ValueError('Imports absent from verified host/own classes: ' + ', '.join(missing))
    return sorted(imports)


def test_swf(abc):
    """Original blank AIR root. Contains only supplied original ABC, no host tags."""
    def tag(code, payload=b''):
        return (struct.pack('<H', (code << 6) | min(len(payload), 63)) +
                (struct.pack('<I', len(payload)) if len(payload) >= 63 else b'') + payload)
    nbits = 15
    bits = f'{nbits:05b}' + ''.join(f'{v:0{nbits}b}' for v in [0, 16000, 0, 12000])
    bits += '0' * (-len(bits) % 8)
    header = int(bits, 2).to_bytes(len(bits) // 8, 'big') + struct.pack('<HH', 24 << 8, 1)
    body = (header + tag(69, struct.pack('<I', 8)) +
            tag(82, struct.pack('<I', 0) + b'bsui_tests\0' + abc) +
            tag(76, struct.pack('<HH', 1, 0) + b'bannersagaui.tests.PreviewContractTests\0') +
            tag(1) + tag(0))
    return b'FWS' + bytes([20]) + struct.pack('<I', len(body) + 8) + body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True, help='FFDec distribution directory')
    parser.add_argument('--jvm', type=Path, required=True, help='Java 17 JVM library')
    parser.add_argument('--jpype-dir', type=Path, help='Optional private pip --target directory')
    parser.add_argument('--out', type=Path, required=True, help='New/empty local output directory')
    parser.add_argument('--mode', choices=['contract-tests', 'native-module'], required=True)
    args = parser.parse_args()
    host, ffdec, jvm, out = [p.resolve() for p in (args.host, args.ffdec, args.jvm, args.out)]
    if sha(host) != HOST_SHA256:
        raise ValueError('Only verified original TBS1 2.58.17 input is supported')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory must be empty')
    paths = [ROOT / 'src/bannersagaui/preview' / (name + '.as')
             for name in ['PreviewFrame', 'PreviewSession', 'PreviewLayer']]
    if args.mode == 'contract-tests':
        paths.append(ROOT / 'tests/air/PreviewContractTests.as')
    else:
        paths.append(ROOT / 'src/bannersagaui/preview/FieldPreview.as')
    sources = [(p.name, p.read_text(encoding='utf-8')) for p in paths]
    if args.mode == 'native-module':
        sources.insert(3, ('RamPreviewProvider.as', provider_source(ROOT)))
    own = {'bannersagaui.preview.' + Path(name).stem for name, _ in sources}
    own.discard('bannersagaui.preview.PreviewContractTests')
    if args.mode == 'contract-tests':
        own.add('bannersagaui.tests.PreviewContractTests')
    classes = {name for _, abc in abcs(host) for name in abc.classes}
    imports = validate_imports([source for _, source in sources], classes, own)
    if args.jpype_dir:
        sys.path.insert(0, str(args.jpype_dir.resolve()))
    import jpype
    if jpype.__version__ != '1.6.0':
        raise ValueError('Research compiler requires JPype1 1.6.0')
    jars = sorted((ffdec / 'lib').glob('*.jar'))
    if not jars or not jvm.is_file():
        raise ValueError('Missing FFDec libraries/JVM')
    out.mkdir(parents=True, exist_ok=True)
    previous = Path.cwd()
    try:
        os.chdir(out)  # Confine FFDec logs/cache to ignored research output.
        jpype.startJVM(str(jvm), '-Djava.awt.headless=true', classpath=[str(p) for p in jars])
        J = jpype.JClass
        stream = J('java.io.FileInputStream')(str(host))
        try:
            swf = J('com.jpexs.decompiler.flash.SWF')(stream, False)
        finally:
            stream.close()
        tag = J('com.jpexs.decompiler.flash.tags.DoABC2Tag')(swf)
        abc = tag.getABC()
        index = swf.getAbcIndex()
        index.selectAbc(abc)
        compiler = J('com.jpexs.decompiler.flash.abc.avm2.parser.script.ActionScript3Parser')
        for name, source in sources:
            compiler.compile(source, abc, index, name, len(abc.instance_info),
                             len(abc.script_info), True, swf.getDocumentClass())
        output = out / 'preview.abc'
        stream = J('java.io.FileOutputStream')(str(output))
        try:
            abc.saveToStream(stream)
        finally:
            stream.close()
    finally:
        if jpype.isJVMStarted():
            jpype.shutdownJVM()
        os.chdir(previous)
    actual = set(ABC(output.read_bytes()).classes)
    if actual != own:
        raise ValueError('Isolated ABC class boundary mismatch: ' + repr(actual ^ own))
    outputs = {output.name: sha(output)}
    if args.mode == 'contract-tests':
        harness = out / 'PreviewContractTests.swf'
        harness.write_bytes(test_swf(output.read_bytes()))
        outputs[harness.name] = sha(harness)
    manifest = {'status': 'compiled; not game-runtime acceptance', 'mode': args.mode,
                'host_sha256': sha(host), 'host_modified': False, 'classes': sorted(actual),
                'imports': imports, 'sources': {str(p.relative_to(ROOT)): sha(p) for p in paths},
                'generated_sources': {name: hashlib.sha256(source.encode()).hexdigest()
                                      for name, source in sources if name == 'RamPreviewProvider.as'},
                'generator_inputs': {str(p.relative_to(ROOT)): sha(p) for p in
                                     [Path(__file__).resolve(), ROOT / 'tools/research/preview_module_source.py',
                                      ROOT / 'tools/research/ram_probe_body.as.inc',
                                      ROOT / 'tools/research/build_ram_probe.py',
                                      ROOT / 'tools/research/abc_index.py']},
                'toolchain': {'jpype': jpype.__version__, 'jvm_sha256': sha(jvm),
                              'ffdec_jars': {p.name: sha(p) for p in jars}}, 'outputs': outputs}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'classes': sorted(actual), 'outputs': outputs}))


if __name__ == '__main__':
    main()
