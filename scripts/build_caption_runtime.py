#!/usr/bin/env python3
"""从固定上游提交和已校验补丁构建独立版本；不修改源仓库或安装全局工具。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.0-craft.1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(repository, output, manifest_name="caption-font-patch.json", version=VERSION):
    manifest = json.loads((ROOT / 'runtime' / manifest_name).read_text())
    patch = ROOT / manifest['patch']
    if sha(patch) != manifest['patchSha256']:
        raise ValueError('patch_checksum_mismatch')
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('unsupported_build_platform')
    if output.exists():
        raise ValueError('output_exists')
    commit = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', manifest['upstreamCommit'] + '^{commit}'], text=True).strip()
    if commit != manifest['upstreamCommit']:
        raise ValueError('upstream_commit_mismatch')
    with tempfile.TemporaryDirectory(prefix='filmcraft-caption-build-') as temporary:
        staging = Path(temporary)
        source = staging / 'source'
        source.mkdir()
        archive = staging / 'upstream.tar'
        subprocess.run(['git', '-C', str(repository), 'archive', commit, '-o', str(archive)], check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(source, filter='data')
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
        cargo = source / 'Cargo.toml'
        text = cargo.read_text()
        original = 'version = "0.2.0"'
        if text.count(original) != 1:
            raise ValueError('workspace_version_mismatch')
        cargo.write_text(text.replace(original, 'version = "' + version + '"'))
        env = dict(os.environ, RUSTFLAGS='--remap-path-prefix=' + str(source) + '=/craft-source')
        subprocess.run(['cargo', 'test', '--offline', '-p', 'filmcraft-captions'], cwd=source, env=env, check=True)
        if manifest_name == 'sequence-rate-patch.json':
            subprocess.run(['cargo', 'test', '--offline', '-p', 'filmcraft-engine', 'image_sequence_tests'], cwd=source, env=env, check=True)
        subprocess.run(['cargo', 'build', '--offline', '--release', '-p', 'filmcraft-cli'], cwd=source, env=env, check=True)
        binary = source / 'target/release/filmcraft-cli'
        version_output = subprocess.check_output([str(binary), '--version'], text=True).strip()
        if version_output != 'filmcraft-cli ' + version:
            raise ValueError('candidate_version_mismatch')
        provenance = dict(manifest, runtimeVersion=version, status='built-maintained-runtime', binarySha256=sha(binary), rustc=subprocess.check_output(['rustc', '--version'], text=True).strip(), platform='darwin-arm64', cargoLockSha256=sha(source / 'Cargo.lock'), sourceArchiveSha256=sha(archive))
        output.mkdir(parents=True)
        package = output / ('filmcraft-cli-' + version + '-macos-arm64.zip')
        with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as target:
            entries = {'filmcraft-cli': binary.read_bytes(), 'LICENSE-MIT': (source / 'LICENSE-MIT').read_bytes(), 'LICENSE-APACHE': (source / 'LICENSE-APACHE').read_bytes(), 'PROVENANCE.json': (json.dumps(provenance, ensure_ascii=False, indent=2) + '\n').encode(), patch.name: patch.read_bytes()}
            for license_file in sorted((source / 'assets/fonts').glob('OFL-*.txt')):
                entries['LICENSE-' + license_file.name] = license_file.read_bytes()
            entries['LICENSE-ATTRIBUTION.md'] = (source / 'ATTRIBUTION.md').read_bytes()
            for name, content in entries.items():
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 6, 0, 0, 0))
                info.external_attr = (0o100755 if name == 'filmcraft-cli' else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(info, content)
        receipt = {'schema': 'craft-maintained-runtime-build/v1', 'runtimeVersion': version, 'platform': 'darwin-arm64', 'archive': package.name, 'archiveSha256': sha(package), 'binarySha256': sha(binary), 'versionOutput': version_output, 'provenance': provenance, 'provenanceSha256': hashlib.sha256(entries['PROVENANCE.json']).hexdigest()}
        (output / 'build-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repository.absolute(), args.output.absolute()), ensure_ascii=False))
