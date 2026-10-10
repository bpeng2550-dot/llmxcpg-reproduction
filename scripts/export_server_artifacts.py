#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Export a small allowlist of real artifacts for private review, without GPU work."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import sys
import zipfile

MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
PREDICTIONS = 'QwQ-32B-Preview-bnb-4bit_formai_avengers_test_instruction_predictions.jsonl'
PACKAGES = ('torch', 'transformers', 'peft', 'bitsandbytes', 'accelerate', 'huggingface-hub', 'numpy', 'tqdm', 'jsonlines', 'scikit-learn')


def beneath(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def collect(root, run_dir, output):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('experiment root does not exist')
    run = (root / run_dir).resolve()
    if not beneath(run, root / 'results') or run == root / 'results':
        raise ValueError('run directory must be inside the experiment results directory')
    output = Path(output).resolve()
    if not beneath(output, root / 'github') or output == root / 'github':
        raise ValueError('output must be a new ZIP under the experiment root github directory')
    if output.exists():
        raise ValueError('output already exists; choose a new filename')
    if output.suffix.lower() != '.zip':
        raise ValueError('output must have a .zip extension')
    frozen = root / 'src-frozen' / 'llmxcpg-main'
    candidates = [
        ('inference/detect_local_offline.py', root / 'work' / 'detect_local_offline.py', True),
        ('upstream/detect_inference.py', frozen / 'inference' / 'detect_inference.py', True),
        ('prompts/detect_system_prompt.txt', frozen / 'prompts' / 'detect_system_prompt.txt', True),
        ('upstream/LICENSE', frozen / 'LICENSE', True),
        ('evidence/threshold_recheck_050_0547.json', run / 'threshold_recheck_050_0547.json', True),
        ('evidence/predictions.jsonl', run / PREDICTIONS, True),
        ('evidence/run.log', run / 'run.log', True),
        ('evidence/formai_input.json', frozen / 'data' / 'formai_avengers_test_instruction.json', True),
        ('configs/adapter_config.json', root / 'models' / 'LLMxCPG-D' / 'adapter_config.json', False),
        ('configs/base_model_config.json', root / 'models' / 'QwQ-32B-Preview-bnb-4bit' / 'config.json', False),
        ('evidence/formai_smoke4_manifest.json', root / 'work' / 'formai_smoke4_manifest.json', False),
    ]
    if run.is_dir():
        for path in sorted(run.glob('*.tsv')):
            candidates.append(('evidence/tsv/' + path.name, path, False))
    manifest = {
        'purpose': 'Private original-material transfer; do not publish this ZIP directly',
        'collected_at_utc': datetime.now(timezone.utc).isoformat(),
        'experiment_root': str(root), 'run_directory': str(run),
        'files': [], 'missing_required': [], 'missing_optional': [],
        'syntax_errors': [], 'environment': {'python': platform.python_version(), 'packages': {}},
        'gpu_inference_executed': False,
    }
    for package in PACKAGES:
        try:
            manifest['environment']['packages'][package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            manifest['environment']['packages'][package] = None
    payloads = []
    total = 0
    for name, source, required in candidates:
        if not beneath(source, root):
            raise ValueError(f'allowlisted file resolves outside experiment root: {name}')
        if not source.is_file():
            manifest['missing_required' if required else 'missing_optional'].append(name)
            continue
        if source.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f'file exceeds 16 MiB collection limit: {name}')
        data = source.read_bytes()
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError('allowlisted artifacts exceed 64 MiB collection limit')
        manifest['files'].append({'archive_path': name, 'source_relative_path': str(source.relative_to(root)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        if source.suffix == '.py':
            try:
                ast.parse(data, filename=name)
            except (SyntaxError, ValueError) as exc:
                manifest['syntax_errors'].append({'file': name, 'message': str(exc)})
        payloads.append((name, data))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payloads:
            archive.writestr(name, data)
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/data/llmxcpg-repro'))
    parser.add_argument('--run-dir', default='results/formai_full383_20261010_104348')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        manifest, output = collect(args.root, args.run_dir, args.output)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    print(f'Exported: {output}')
    print(f'Files: {len(manifest["files"])}; uncompressed bytes: {sum(item["bytes"] for item in manifest["files"])}')
    print('Missing required: ' + json.dumps(manifest['missing_required'], ensure_ascii=False))
    print('Python syntax issues: ' + json.dumps(manifest['syntax_errors'], ensure_ascii=False))
    print('No model loading or GPU inference was performed. Keep this ZIP private for review.')
    return 2 if manifest['missing_required'] or manifest['syntax_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
