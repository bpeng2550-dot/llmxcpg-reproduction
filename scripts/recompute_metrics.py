#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Recompute fixed thresholds from saved predictions; no model or GPU needed."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys


def read_rows(path):
    rows = []
    with Path(path).open('r', encoding='utf-8-sig') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'line {number}: invalid JSON') from exc
            if not isinstance(row, dict):
                raise ValueError(f'line {number}: expected JSON object')
            label = row.get('label')
            probability = row.get('probability_vulnerable')
            if type(label) is not int or label not in (0, 1):
                raise ValueError(f'line {number}: label must be integer 0 or 1')
            if type(probability) not in (int, float) or not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError(f'line {number}: probability_vulnerable must be finite and within [0, 1]')
            rows.append((label, float(probability)))
    if not rows:
        raise ValueError('prediction file contains no samples')
    return rows


def calculate(rows, threshold, rule):
    counts = dict(tp=0, fp=0, fn=0, tn=0)
    for label, probability in rows:
        if rule == '>=':
            prediction = int(probability >= threshold)
        elif rule == '>':
            prediction = int(probability > threshold)
        else:
            raise ValueError('unsupported threshold rule')
        key = ('tp' if label else 'fp') if prediction else ('fn' if label else 'tn')
        counts[key] += 1
    tp, fp, fn, tn = (counts[key] for key in ('tp', 'fp', 'fn', 'tn'))
    total = len(rows)
    return {
        'threshold': threshold, 'rule': rule, 'total_samples': total,
        'predicted_vulnerable': tp + fp, 'predicted_benign': tn + fn,
        'accuracy': (tp + tn) / total,
        'precision': tp / (tp + fp) if tp + fp else 0.0,
        'recall': tp / (tp + fn) if tp + fn else 0.0,
        'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        'confusion_matrix': counts,
    }


def summarize(path, expected_samples=None):
    path = Path(path)
    rows = read_rows(path)
    if expected_samples is not None and len(rows) != expected_samples:
        raise ValueError(f'expected {expected_samples} samples, found {len(rows)}')
    return {
        'evidence_status': 'recomputed_from_saved_prediction_file',
        'prediction_file': path.name,
        'prediction_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'class_distribution': {
            'benign': sum(label == 0 for label, _ in rows),
            'vulnerable': sum(label == 1 for label, _ in rows),
        },
        'probability_boundaries': {
            'equals_0_5': sum(probability == .5 for _, probability in rows),
            'equals_0_547': sum(probability == .547 for _, probability in rows),
        },
        'original_threshold': calculate(rows, .5, '>='),
        'paper_threshold': calculate(rows, .547, '>'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', required=True, type=Path)
    parser.add_argument('--expected-samples', type=int)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--csv', type=Path)
    args = parser.parse_args()
    if args.expected_samples is not None and args.expected_samples < 1:
        parser.error('--expected-samples must be positive')
    outputs = [args.output] + ([args.csv] if args.csv else [])
    if len({path.resolve() for path in outputs}) != len(outputs):
        parser.error('JSON and CSV output paths must differ')
    for path in outputs:
        if path.exists() or path.resolve() == args.predictions.resolve():
            parser.error(f'output already exists or aliases input: {path.name}')
    try:
        report = summarize(args.predictions, args.expected_samples)
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        if args.csv:
            fields = ['threshold', 'rule', 'total_samples', 'predicted_vulnerable', 'predicted_benign', 'accuracy', 'precision', 'recall', 'f1', 'tp', 'fp', 'fn', 'tn']
            with args.csv.open('x', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for key in ('original_threshold', 'paper_threshold'):
                    value = report[key]
                    row = {field: value[field] for field in fields if field in value}
                    row.update(value['confusion_matrix'])
                    writer.writerow(row)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
