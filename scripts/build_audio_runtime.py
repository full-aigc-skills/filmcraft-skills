#!/usr/bin/env python3
"""从固定源码和字幕／序列／音频采样补丁构建独立维护版，不替换旧运行时。"""
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
                           manifest_name='audio-sample-patch.json', version='0.2.0-craft.3', target_directory=args.target_directory), ensure_ascii=False))
