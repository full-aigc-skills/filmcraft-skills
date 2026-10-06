"""声明式运动与 LUT 的输入边界。"""
import importlib.util
from pathlib import Path
import unittest

class MotionLutTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('motion_workflow',Path(__file__).resolve().parents[1]/'skills/filmcraft-use/scripts/workflow.py')
        self.w=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.w)

    def plan(self,command,params):
        return {'operations':[{'command':command,'params':params}]}

    def test_motion_requires_explicit_target_and_finite_values(self):
        params={'clip':{'$ref':'shotClip.clips.0'},'effect':'motion','param':'position','value':[100,90],'time':'254016000000'}
        self.w.validate(self.plan('effects.setParam',params))
        for key,value in [('clip',None),('clip',True),('value',[float('nan'),90]),('value',10**1000),('effect',-1),('param',''),('unknown',1)]:
            with self.subTest(key=key,value=str(value)[:30]),self.assertRaisesRegex(ValueError,'invalid_effect_params'):
                self.w.validate(self.plan('effects.setParam',{**params,key:value}))
        for value in (1,True,'-1','1.5','01'):
            with self.assertRaisesRegex(ValueError,'ticks_require_decimal_string'):
                self.w.validate(self.plan('effects.setParam',{**params,'time':value}))

    def test_toggle_is_explicit_and_does_not_accept_value(self):
        params={'clip':2,'effect':'motion','param':'position'}
        self.w.validate(self.plan('effects.toggleAnimation',params))
        with self.assertRaisesRegex(ValueError,'invalid_effect_params'):
            self.w.validate(self.plan('effects.toggleAnimation',{**params,'value':1}))

    def test_lut_must_be_registered_and_cannot_be_imported_as_media(self):
        plan=self.plan('lumetri.setInputLut',{'clip':2,'asset':'grade'})
        with self.assertRaisesRegex(ValueError,'registered_lut_required'):
            self.w.validate(plan)
        plan['assets']={'grade':{'kind':'lut','path':'grade.cube','sha256':'a'*64}}
        self.w.validate(plan)
        with self.assertRaisesRegex(ValueError,'invalid_lut_params'):
            self.w.validate({**plan,'operations':[{'command':'lumetri.setInputLut','params':{'clip':2,'path':'outside.cube'}}]})
        with self.assertRaisesRegex(ValueError,'lut_is_not_media'):
            self.w.validate({**plan,'operations':[{'command':'asset.import','params':{'asset':'grade'}}]})

if __name__=='__main__':unittest.main()
