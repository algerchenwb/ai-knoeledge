import csv
import io
import json
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import unittest
from business_export_demo import Exports, Principal, demo, text_cell


class Checks(unittest.TestCase):
    def setUp(self):
        self.p=Principal('t','u',True,frozenset({'a','b'}))
        self.e=Exports()
        self.rows=[dict(tenant='t',object_id='a',name='中文,地点',count=25,secret='excluded')]
        self.job=self.create()

    def create(self, **kwargs):
        args=dict(p=self.p,request='r',version='v1',object_ids=['a'],source_rows=self.rows,now=100,ttl=60)
        args.update(kwargs)
        return self.e.create(**args)

    def test_01_queued_not_downloadable(self):
        self.assertEqual(self.e.status(self.p,self.job,100)['state'],'queued')
        with self.assertRaises(ValueError): self.e.download(self.p,self.job,100)

    def test_02_csv_and_whitelist(self):
        self.e.run(self.p,self.job,101)
        data=self.e.download(self.p,self.job,102).decode()
        self.assertEqual(list(csv.reader(io.StringIO(data))),[['object_id','name','count'],['a','中文,地点','25']])
        self.assertNotIn('excluded',data)

    def test_03_snapshot_mutation(self):
        self.rows[0]['count']=999
        self.e.run(self.p,self.job,101)
        self.assertIn(',25\r\n',self.e.download(self.p,self.job,101).decode())

    def test_04_idempotent_create(self):
        self.assertEqual(self.create(),self.job)

    def test_05_changed_snapshot_conflict(self):
        self.rows[0]['count']=26
        with self.assertRaises(ValueError): self.create()

    def test_06_changed_version_conflict(self):
        with self.assertRaises(ValueError): self.create(version='v2')

    def test_07_worker_retry(self):
        first=self.e.run(self.p,self.job,101)
        self.assertEqual(self.e.run(self.p,self.job,102),first)

    def test_08_current_permission(self):
        self.e.run(self.p,self.job,101)
        denied=replace(self.p,can_export=False)
        for action in [self.e.status,self.e.run,self.e.download]:
            with self.assertRaises(PermissionError): action(denied,self.job,102)

    def test_09_object_revocation(self):
        denied=replace(self.p,objects=frozenset({'b'}))
        for action in [self.e.status,self.e.run,self.e.download]:
            with self.assertRaises(PermissionError): action(denied,self.job,101)
        self.assertEqual(self.e.status(self.p,self.job,101)['state'],'queued')

    def test_10_tenant_and_user_scope(self):
        for p in [replace(self.p,tenant='other'),replace(self.p,user='other')]:
            with self.assertRaises(PermissionError): self.e.status(p,self.job,100)
        with self.assertRaises(PermissionError): self.e.status(self.p,'unknown',100)

    def test_11_expiry_boundary(self):
        self.e.run(self.p,self.job,101)
        self.e.download(self.p,self.job,159)
        self.assertEqual(self.e.status(self.p,self.job,160)['state'],'expired')
        with self.assertRaises(ValueError): self.e.download(self.p,self.job,160)
        with self.assertRaises(ValueError): self.e.run(self.p,self.job,160)

    def test_12_scope_filter(self):
        rows=self.rows+[dict(tenant='other',object_id='a',name='foreign',count=1),dict(tenant='t',object_id='b',name='notselected',count=2)]
        job=self.create(request='filter',source_rows=rows)
        self.e.run(self.p,job,101)
        data=self.e.download(self.p,job,101).decode()
        self.assertNotIn('foreign',data); self.assertNotIn('notselected',data)
        with self.assertRaises(PermissionError): self.create(request='unauthorized',object_ids=['c'])

    def test_13_missing_duplicate(self):
        with self.assertRaises(ValueError): self.create(request='missing',object_ids=['b'])
        with self.assertRaises(ValueError): self.create(request='duplicate',source_rows=self.rows*2)
        with self.assertRaises(ValueError): self.create(object_ids=['a','a'])

    def test_14_formula_prefixes(self):
        for s in ['=1+1','+1','-1','@SUM(A1)','  =1','\t=1','\rhello','\nhello']:
            self.assertEqual(text_cell(s),"'"+s)
        self.assertEqual(text_cell('普通文字'),'普通文字')

    def test_15_formula_in_actual_csv(self):
        job=self.create(request='formula',source_rows=[dict(tenant='t',object_id='a',name='=SUM(1,2)',count=25)])
        self.e.run(self.p,job,101)
        parsed=list(csv.reader(io.StringIO(self.e.download(self.p,job,101).decode())))
        self.assertEqual(parsed[1][1],"'=SUM(1,2)")
        self.assertEqual(parsed[1][2],'25')

    def test_16_strict_inputs(self):
        for ttl in [True,0,3601,1.5]:
            with self.assertRaises(ValueError): self.create(ttl=ttl)
        with self.assertRaises(ValueError): self.create(now=True)
        with self.assertRaises(ValueError): self.create(object_ids=[])
        with self.assertRaises(ValueError): self.create(source_rows=[dict(tenant='t',object_id='a',name='a',count=True)])

    def test_17_clock(self):
        with self.assertRaises(ValueError): self.e.status(self.p,self.job,99)
        self.e.run(self.p,self.job,110)
        with self.assertRaises(ValueError): self.e.download(self.p,self.job,109)

    def test_18_concurrent_create_and_run(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=list(pool.map(lambda _:self.create(),range(2)))
            states=list(pool.map(lambda _:self.e.run(self.p,self.job,101),range(2)))
        self.assertEqual(jobs,[self.job,self.job]); self.assertEqual(states[0],states[1])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful(): raise SystemExit(1)
    Path(__file__).with_name('business-export-results.json').write_text(json.dumps({'date':'2026-10-05','checks_passed':result.testsRun,'example':demo()},ensure_ascii=False,indent=2)+'\n')
