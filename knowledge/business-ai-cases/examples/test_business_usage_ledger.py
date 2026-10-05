import json
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from business_usage_ledger import Ledger, demo


class Checks(unittest.TestCase):
    def setUp(self):
        self.l = Ledger()
        self.l.configure('t', 'p', 100)

    def tearDown(self):
        self.l.close()

    def hold(self, request='r', amount=40):
        return self.l.reserve('t', 'p', request, 'f', amount)

    def test_01_reservation(self):
        self.hold()
        self.assertEqual(self.l.balance('t', 'p'), {'quota':100,'held':40,'used':0,'available':60})

    def test_02_reserve_retry(self):
        self.hold(); self.assertTrue(self.hold()['replayed'])
        self.assertEqual(self.l.balance('t','p')['held'],40)

    def test_03_payload_conflict(self):
        self.hold()
        with self.assertRaises(ValueError): self.l.reserve('t','p','r','different',40)

    def test_04_amount_conflict(self):
        self.hold()
        with self.assertRaises(ValueError): self.hold(amount=41)

    def test_05_settlement(self):
        self.hold(); self.l.finish('t','p','r',25)
        self.assertEqual(self.l.balance('t','p'), {'quota':100,'held':0,'used':25,'available':75})

    def test_06_settlement_retry(self):
        self.hold(); self.l.finish('t','p','r',25)
        self.assertTrue(self.l.finish('t','p','r',25)['replayed'])
        self.assertEqual(self.l.balance('t','p')['used'],25)

    def test_07_settlement_conflict(self):
        self.hold(); self.l.finish('t','p','r',25)
        with self.assertRaises(ValueError): self.l.finish('t','p','r',26)

    def test_08_release(self):
        self.hold(); self.l.finish('t','p','r',confirmed_unused=True)
        self.assertTrue(self.l.finish('t','p','r',confirmed_unused=True)['replayed'])
        self.assertEqual(self.l.balance('t','p')['available'],100)

    def test_09_terminal_conflict(self):
        self.hold(); self.l.finish('t','p','r',confirmed_unused=True)
        with self.assertRaises(ValueError): self.l.finish('t','p','r',1)
        self.assertEqual(self.hold()['state'],'released')

    def test_10_quota(self):
        self.hold(amount=70)
        self.assertEqual(self.hold('other',40)['state'],'denied')
        self.assertEqual(self.l.balance('t','p')['held'],70)

    def test_11_unknown_usage_remains_held(self):
        self.hold()
        with self.assertRaises(ValueError): self.l.finish('t','p','r')
        self.assertEqual(self.l.balance('t','p')['held'],40)

    def test_12_over_cap(self):
        self.hold()
        with self.assertRaises(ValueError): self.l.finish('t','p','r',41)
        self.assertEqual(self.l.balance('t','p')['held'],40)

    def test_13_scope(self):
        self.l.configure('u','p',100); self.l.configure('t','next',100)
        self.hold()
        self.l.reserve('u','p','r','f',20)
        self.assertEqual(self.l.balance('u','p')['held'],20)
        self.assertEqual(self.l.balance('t','next')['held'],0)
        with self.assertRaises(ValueError): self.l.finish('t','p','unknown',1)

    def test_14_inputs_and_policy(self):
        for amount in [True, -1, 1.5, '10',0]:
            with self.assertRaises(ValueError): self.hold(amount=amount)
        with self.assertRaises(ValueError): self.l.configure('t','p',99)
        with self.assertRaises(ValueError): self.l.reserve('','p','r','f',1)
        with self.assertRaises(ValueError): self.l.reserve('x','p','r','f',1)

    def test_15_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'ledger.db')
            first=Ledger(path); first.configure('t','p',100); first.reserve('t','p','r','f',40); first.close()
            second=Ledger(path)
            try:
                self.assertTrue(second.reserve('t','p','r','f',40)['replayed'])
                second.finish('t','p','r',25)
                self.assertEqual(second.balance('t','p')['used'],25)
            finally: second.close()

    def test_16_concurrent_quota(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'ledger.db')
            initial=Ledger(path); initial.configure('t','p',100); initial.close()
            def attempt(request):
                ledger=Ledger(path)
                try: return ledger.reserve('t','p',request,'f',70)['state']
                finally: ledger.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                states=list(pool.map(attempt,['one','two']))
            self.assertEqual(sorted(states),['denied','held'])
            final=Ledger(path)
            try: self.assertEqual(final.balance('t','p')['available'],30)
            finally: final.close()


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful(): raise SystemExit(1)
    Path(__file__).with_name('business-usage-results.json').write_text(json.dumps({'date':'2026-10-05','checks_passed':result.testsRun,'example':demo()}, ensure_ascii=False,indent=2)+'\n')
