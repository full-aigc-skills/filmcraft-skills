"""运行时补丁和构建边界；不在单元测试中编译原生仓库。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import shutil
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

    def test_resample_builder_isolated_entrypoint_and_cumulative_regression(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'scripts/build_resample_runtime.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--target-directory', result.stdout)
        manifest = json.loads((ROOT / 'runtime/audio-resample-edit-list-patch.json').read_text())
        self.assertEqual(manifest['runtimeVersion'], '0.2.0-craft.6')
        self.assertEqual(manifest['cargoFeatures'], ['whisper'])
        prior = (ROOT / 'runtime/patches/pcm-packet-timing.patch').read_bytes()
        data = (ROOT / manifest['patch']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['patchSha256'])
        self.assertEqual(hashlib.sha256(prior).hexdigest(), manifest['includedPcmPacketTimingPatchSha256'])
        self.assertTrue(data.startswith(prior))
        self.assertIn(b'edit_offset_moves_the_window_without_changing_resample_phase', data)
        self.assertIn(b'primed_aac_resampling_matches_native_samples_across_request_boundaries', data)

    def test_resample_build_executes_all_inherited_regressions_before_packaging(self):
        manifest = json.loads((ROOT / 'runtime/audio-resample-edit-list-patch.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'fixture'
            fixture.mkdir()
            for name, text in {'Cargo.toml': 'version = "0.2.0"\n', 'Cargo.lock': 'lock', 'LICENSE-MIT': 'mit', 'LICENSE-APACHE': 'apache', 'ATTRIBUTION.md': 'credits'}.items():
                (fixture / name).write_text(text)
            target = root / 'target'
            (target / 'release').mkdir(parents=True)
            (target / 'release/filmcraft-cli').write_bytes(b'candidate binary')
            commands = []

            def run(command, **kwargs):
                commands.append(command)
                if command[0] == 'cargo':
                    self.assertEqual(kwargs['env']['FILMCRAFT_REQUIRE_ORACLES'], '1')
                if command[:2] == ['git', '-C'] and 'archive' in command:
                    Path(command[-1]).write_bytes(b'upstream archive')
                return subprocess.CompletedProcess(command, 0)

            with patch.object(self.module.platform, 'system', return_value='Darwin'), patch.object(self.module.platform, 'machine', return_value='arm64'), patch.object(self.module.subprocess, 'run', side_effect=run), patch.object(self.module.subprocess, 'check_output', side_effect=[manifest['upstreamCommit'] + '\n', 'filmcraft-cli 0.2.0-craft.6\n', 'rustc test\n']), patch.object(self.module.tarfile, 'open') as archive:
                archive.return_value.__enter__.return_value.extractall.side_effect = lambda source, **kwargs: shutil.copytree(fixture, source, dirs_exist_ok=True)
                receipt = self.module.build(root, root / 'output', manifest_name='audio-resample-edit-list-patch.json', version='0.2.0-craft.6', target_directory=target)
            self.assertEqual([command for command in commands if command[:2] == ['cargo', 'test']], [
                ['cargo', 'test', '--offline', '-p', 'filmcraft-captions'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-engine', 'image_sequence_tests'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-project'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-speech', '--features', 'whisper,download', '--lib'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-engine', '--features', 'whisper,speech-download', 'transcript'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-codecs', '--test', 'pcm_packet_timing'],
                ['cargo', 'test', '--offline', '-p', 'filmcraft-codecs', '--test', 'mp4_audio_edit_resample'],
            ])
            self.assertEqual(commands[-1], ['cargo', 'build', '--offline', '--release', '-p', 'filmcraft-cli', '--features', 'whisper'])
            self.assertEqual(receipt['runtimeVersion'], '0.2.0-craft.6')

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
