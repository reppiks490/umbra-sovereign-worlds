import unittest, torch
import evolution_graph_training_v94 as base
import evolution_scale_training_v95 as m

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)
    def test_equivariance_in_message_and_rollout(self):
        net=m.model(7);w,s,y=base.batch(8,3,271)
        x=torch.tensor([[0.,0.],[1.,2.],[2.,0.]],dtype=torch.float64)
        self.assertTrue(torch.allclose(net(x*5),net(x)*5,atol=1e-10))
        self.assertTrue(torch.allclose(base.rollout(net,m.scaled(w,5),s)[-1],base.rollout(net,w,s)[-1]*5,atol=1e-9))
    def test_matched_initialization_and_updates(self):
        a=base.model(8);b=m.model(8);before=base.weights(a)
        self.assertEqual(before,base.weights(b));self.assertEqual(len(before),65)
        ra=base.train(a,'teacher',8,steps=4,batch_size=3)
        rb=base.train(b,'teacher',8,steps=4,batch_size=3)
        self.assertEqual(ra['batch_fingerprints'],rb['batch_fingerprints'])
        self.assertNotEqual(before,base.weights(a));self.assertNotEqual(before,base.weights(b))
    def test_fresh_holdout_and_exact_reference(self):
        self.assertTrue(set(m.TRAIN_SEEDS).isdisjoint(base.TRAIN_SEEDS+base.EVAL_SEEDS+m.EVAL_SEEDS))
        self.assertTrue(set(m.EVAL_SEEDS).isdisjoint(base.TRAIN_SEEDS+base.EVAL_SEEDS))
        rows=m.evaluate(m.model(9),9,graphs=2)
        self.assertEqual(len(rows),12)
        self.assertTrue(all(x['reference_mae']<1e-8 and x['equivariance_error']<1e-8 for x in rows))
        for n in base.SIZES:
            group=[x for x in rows if x['n']==n]
            self.assertEqual(len({x['base_graph_sha256'] for x in group}),1)
    def test_invalid_scale(self):
        w,s,y=base.batch(4,1,2)
        for f in (0,True,2,10):
            with self.assertRaises(ValueError):m.scaled(w,f)
    def test_actual_experiment_retains_both_arms(self):
        r,w=m.experiment(steps=2,batch_size=2,graphs=1)
        self.assertEqual(r['optimizer_steps'],12)
        self.assertEqual(r['base_eval_graphs_per_arm'],12)
        self.assertEqual(r['scaled_eval_observations_per_arm'],36)
        self.assertFalse(r['promotion_authorized']);self.assertFalse(r['semantic_mastery_certified'])
        self.assertEqual(len(w),3)
        self.assertTrue(all(len(x['unstructured'])==65 and len(x['homogeneous'])==65 for x in w))
if __name__=='__main__':unittest.main()
