"""完整命令和所属桌面必须消费可信只读模型缓存，不得悄然换成空目录。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/filmcraft-use/scripts'

def load(name):
    spec = importlib.util.spec_from_file_location('model_directory_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class CommandModelDirectoryTests(unittest.TestCase):
    def test_outside_model_reference_refuses_before_install_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); allowed = root / 'allowed'; allowed.mkdir()
            models = root / 'outside-models'; models.mkdir()
            skill = root/'single-skill'; shutil.copytree(SCRIPTS.parent,skill,ignore=shutil.ignore_patterns('__pycache__','*.pyc')); (skill/'scripts/bootstrap.py').write_text("def install(*args,**kwargs): raise ValueError('owned_installer_would_run')\n")
            plan = allowed / 'plan.json'; plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'Owned'}}]}))
            output = allowed / 'delivery'; runtime = allowed / 'runtime'
            result = subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/commands.py'),'run',str(plan),'--output',str(output),'--runtime-home',str(runtime),'--read-root',str(allowed),'--write-root',str(allowed)], env={**os.environ,'FILMCRAFT_DATA_DIR':str(models)},capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['error'],'permission_read_denied')
            self.assertFalse(output.exists()); self.assertFalse(runtime.exists())

    def test_invalid_model_reference_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); plan = root / 'plan.json'
            skill=root/'single-skill';shutil.copytree(SCRIPTS.parent,skill,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));(skill/'scripts/bootstrap.py').write_text("def install(*args,**kwargs): raise ValueError('owned_installer_would_run')\n")
            plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'Owned'}}]}))
            output = root / 'delivery'; runtime = root / 'runtime'
            result = subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/commands.py'),'run',str(plan),'--output',str(output),'--runtime-home',str(runtime),'--read-root',str(root),'--write-root',str(root)],env={**os.environ,'FILMCRAFT_DATA_DIR':'relative-untrusted-model-cache'},capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['error'],'invalid_execution_permissions')
            self.assertFalse(output.exists()); self.assertFalse(runtime.exists())

    def test_command_native_argv_uses_and_protects_explicit_readonly_cache(self):
        commands = load('commands'); helper = load('execution_permissions')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); models = root/'models'; models.mkdir()
            cache = root/'runtime'; cache.mkdir(); output=root/'delivery'
            policy={'schema':helper.SCHEMA,'readRoots':[str(root)],'writeRoots':[str(root)]}
            observed={}
            def capture(argv, policy, **kwargs):
                observed.update(argv=argv, protected=kwargs['protected_roots'])
                raise RuntimeError('owned test stops before native launch')
            helper.ensure_available=lambda:None; helper.command=capture
            original=commands.load
            with patch.dict(os.environ,{'FILMCRAFT_DATA_DIR':str(models)}),patch.object(commands,'load',side_effect=lambda name:helper if name=='execution_permissions' else original(name)):
                commands.execute({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'Owned'}}]},output,cache,permissions=policy,installer=lambda *args:{'executable':sys.executable,'binarySha256':'a'*64})
            self.assertEqual(observed['argv'][observed['argv'].index('--data-dir')+1],str(models))
            self.assertIn(str(models),observed['protected'])

    def test_owned_desktop_uses_and_protects_same_explicit_model_cache(self):
        desktop = load('desktop_session'); helper=load('execution_permissions')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve(); models=root/'models';models.mkdir();output=root/'delivery';output.mkdir()
            policy={'schema':helper.SCHEMA,'readRoots':[str(root)],'writeRoots':[str(root)]};observed={}
            def capture(argv, policy, **kwargs):
                observed.update(argv=argv,protected=kwargs['protected_roots'])
                raise RuntimeError('owned test stops before desktop launch')
            helper.command=capture;original=desktop.load
            with patch.dict(os.environ,{'FILMCRAFT_DATA_DIR':str(models)}),patch.object(desktop,'load',side_effect=lambda name:helper if name=='execution_permissions' else original(name)):
                with self.assertRaisesRegex(RuntimeError,'owned test stops'):
                    desktop.OwnedSession([sys.executable],{'executable':sys.executable},'filmcraft',output,32123,permissions=policy).__enter__()
            self.assertEqual(observed['argv'][observed['argv'].index('--data-dir')+1],str(models))
            self.assertIn(str(models),observed['protected'])

if __name__ == '__main__':
    unittest.main()
