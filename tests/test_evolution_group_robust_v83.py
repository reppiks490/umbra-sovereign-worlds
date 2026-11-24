import math, unittest
import evolution_group_robust_v83 as m

class RobustTests(unittest.TestCase):
    def test_adversary_matches_direct_exponentiation(self):
        state=m.update_log_weights([0.,0.,0.],[1.,2.,4.],.2)
        actual=m.probabilities(state)
        raw=[math.exp(.2*x) for x in [1.,2.,4.]]
        for a,b in zip(actual,raw):self.assertAlmostEqual(a,b/sum(raw))
    def test_large_loss_is_stable(self):
        state=m.update_log_weights([0.,0.],[0.,1e6],1.)
        self.assertEqual(m.probabilities(state),[0.,1.])
        state=m.update_log_weights(state,[1e6,0.],1.)
        self.assertEqual(m.probabilities(state),[.5,.5])
    def test_invalid_inputs(self):
        for state,loss,eta in [([0.],[1.],.1),([0.,0.],[1.,float('nan')],.1),([0.,0.],[1.,-1.],.1),([0.,0.],[1.,2.],True),([0.,0.],[1.,2.],0),([0.,0.],[1.,2.],2),([0.,float('inf')],[1.,2.],.1)]:
            with self.subTest(state=state,loss=loss,eta=eta),self.assertRaises(ValueError):m.update_log_weights(state,loss,eta)
    def test_paired_experiment_reproducible_and_bounded(self):
        a=m.experiment(3,steps=20);b=m.experiment(3,steps=20)
        self.assertEqual(a,b)
        self.assertEqual(set(a['arms']),{'pooled','balanced','dro'})
        for arm in a['arms'].values():
            self.assertEqual(len(arm['test_group_mse']),4)
            self.assertEqual(arm['worst_mse'],max(arm['test_group_mse']))
            self.assertEqual(arm['steps'],20)
        self.assertFalse(a['production_authority'])
        self.assertFalse(a['semantic_mastery_certified'])
    def test_train_and_test_differ(self):
        for g in range(4):
            self.assertNotEqual(m.group_data(3,g,'train',16),m.group_data(3,g,'test',16))
        with self.assertRaises(ValueError):m.group_data(True,0,'train',16)
    def test_summary_keeps_losses_and_rejects_duplicates(self):
        a=m.experiment(3,steps=10);b=m.experiment(4,steps=10)
        r=m.summarize([a,b]);self.assertEqual(r['seeds'],2)
        self.assertEqual(sum(r['worst_vs_balanced'].values()),2)
        with self.assertRaises(ValueError):m.summarize([a,a])
if __name__=='__main__':unittest.main()
