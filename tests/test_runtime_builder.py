"""运行时补丁和构建边界；不在单元测试中编译原生仓库。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class RuntimeBuilderTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_caption_runtime.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_tampered_patch_is_refused_before_git_or_cargo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'runtime').mkdir()
            (root / 'change.patch').write_bytes(b'changed')
            (root / 'runtime/caption-font-patch.json').write_text(json.dumps({'patch':'change.patch','patchSha256':hashlib.sha256(b'original').hexdigest()}))
            with patch.object(self.module,'ROOT',root), patch.object(self.module.subprocess,'run',side_effect=AssertionError('executed')), patch.object(self.module.subprocess,'check_output',side_effect=AssertionError('executed')):
                with self.assertRaisesRegex(ValueError,'patch_checksum_mismatch'):
                    self.module.build(root,root/'output')
            self.assertFalse((root/'output').exists())

    def test_sequence_patch_checksum_rejected_before_native_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root/'runtime').mkdir(); (root/'change.patch').write_bytes(b'changed')
            (root/'runtime/sequence-rate-patch.json').write_text(json.dumps({'patch': 'change.patch', 'patchSha256': hashlib.sha256(b'original').hexdigest()}))
            with patch.object(self.module, 'ROOT', root), patch.object(self.module.subprocess, 'run', side_effect=AssertionError('executed')), patch.object(self.module.subprocess, 'check_output', side_effect=AssertionError('executed')):
                with self.assertRaisesRegex(ValueError, 'patch_checksum_mismatch'):
                    self.module.build(root, root/'output', manifest_name='sequence-rate-patch.json', version='0.2.0-craft.2')
            self.assertFalse((root/'output').exists())

    def test_audio_builder_isolated_python_entrypoint(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'scripts/build_audio_runtime.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--target-directory', result.stdout)

    def test_audio_patch_checksum_rejected_before_native_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'runtime').mkdir()
            (root / 'change.patch').write_bytes(b'changed')
            (root / 'runtime/audio-sample-patch.json').write_text(json.dumps({'patch': 'change.patch', 'patchSha256': hashlib.sha256(b'original').hexdigest()}))
            with patch.object(self.module, 'ROOT', root), patch.object(self.module.subprocess, 'run', side_effect=AssertionError('executed')):
                with self.assertRaisesRegex(ValueError, 'patch_checksum_mismatch'):
                    self.module.build(root, root / 'output', manifest_name='audio-sample-patch.json', version='0.2.0-craft.3')
            self.assertFalse((root / 'output').exists())

    def test_pcm_builder_isolated_entrypoint_and_cumulative_regression(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'scripts/build_pcm_runtime.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((ROOT / 'runtime/pcm-packet-timing-patch.json').read_text())
        self.assertEqual(manifest['runtimeVersion'], '0.2.0-craft.5')
        self.assertEqual(manifest['cargoFeatures'], ['whisper'])
        data = (ROOT / manifest['patch']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['patchSha256'])
        self.assertIn(b'pcm_packets_are_sample_exact_despite_millisecond_timestamps', data)
        self.assertIn(b'pcm_packet_real_gap_is_not_collapsed', data)
        self.assertIn(b'crates/engine/src/transcript.rs', data)
        self.assertIn(b'crates/captions/src/burn.rs', data)

    def test_whisper_build_preserves_old_defaults_and_enables_real_feature(self):
        base=['cargo','build','--offline','--release','-p','filmcraft-cli']
        self.assertEqual(self.module.cargo_build_arguments({}),base)
        self.assertEqual(self.module.cargo_build_arguments({'cargoFeatures':['whisper']}),base+['--features','whisper'])

    def test_unknown_or_option_like_features_are_refused_before_build(self):
        for value in ('whisper',['--all-features'],['other'],['whisper','whisper'],[None]):
            with self.subTest(features=value),self.assertRaisesRegex(ValueError,'runtime_build_features_invalid'):
                self.module.cargo_build_arguments({'cargoFeatures':value})

    def test_unsupported_platform_is_refused_before_source_export(self):
        with patch.object(self.module.platform,'system',return_value='Linux'), patch.object(self.module.subprocess,'check_output',side_effect=AssertionError('executed')):
            with self.assertRaisesRegex(ValueError,'unsupported_build_platform'):
                self.module.build(ROOT,ROOT/'unused-output')

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            marker=output/'user.txt'
            marker.write_text('preserve')
            with patch.object(self.module.platform,'system',return_value='Darwin'), patch.object(self.module.platform,'machine',return_value='arm64'), patch.object(self.module.subprocess,'check_output',side_effect=AssertionError('executed')):
                with self.assertRaisesRegex(ValueError,'output_exists'):
                    self.module.build(ROOT,output)
            self.assertEqual(marker.read_text(),'preserve')
