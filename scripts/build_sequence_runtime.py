#!/usr/bin/env python3
"""从固定源码和字幕／序列补丁构建独立维护版，不替换旧运行时。"""
import argparse
import json
from pathlib import Path

from build_caption_runtime import build


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repository.absolute(), args.output.absolute(),
                           manifest_name='sequence-rate-patch.json', version='0.2.0-craft.2'), ensure_ascii=False))
