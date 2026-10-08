#!/usr/bin/env python3
"""构建保留全部维护补丁的 PCM 包采样时序修复候选，不替换旧运行时。"""
import argparse
import json
from pathlib import Path

import importlib.util

_spec = importlib.util.spec_from_file_location('caption_runtime_builder', Path(__file__).with_name('build_caption_runtime.py'))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
build = _module.build


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.repository.absolute(), args.output.absolute(),
                           manifest_name='pcm-packet-timing-patch.json', version='0.2.0-craft.5', target_directory=args.target_directory), ensure_ascii=False))
