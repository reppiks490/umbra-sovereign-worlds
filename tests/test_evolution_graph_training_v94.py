import unittest,torch
import evolution_graph_training_v94 as m

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)
    def test_exact_relaxation_matches_independent_reference(self):
        for n in (4,8,16,32):
            w,s,y=m.batch(n,3,700+n,3)
            states=m.teacher_states(w,s)
            self.assertTrue(torch.allclose(states[-1],y,atol=1e-5))
    def test_message_model_is_vertex_permutation_equivariant(self):
        w,s,y=m.batch(8,2,701)
        model=m.model(3)
        p=torch.tensor([4,2,6,1,0,7,5,3])
        d=m.rollout(model,w,s)[-1]
        s2=torch.argmax((p[None,:]==s[:,None]).long(),dim=1)
        d2=m.rollout(model,w[:,p][:,:,p],s2)[-1]
        self.assertTrue(torch.allclose(d[:,p],d2,atol=1e-5))
    def test_training_updates_real_weights_and_preserves_controls(self):
        a=m.model(4);b=m.model(4)
        before=m.weights(a)
        self.assertEqual(before,m.weights(b))
        ra=m.train(a,'teacher',4,steps=4,batch_size=3)
        rb=m.train(b,'rollout',4,steps=4,batch_size=3)
        self.assertEqual(ra['optimizer_steps'],4)
        self.assertEqual(rb['optimizer_steps'],4)
        self.assertNotEqual(before,m.weights(a));self.assertNotEqual(before,m.weights(b))
        self.assertEqual(ra['batch_fingerprints'],rb['batch_fingerprints'])
    def test_invalid_training_and_seed_separation(self):
        self.assertTrue(set(m.TRAIN_SEEDS).isdisjoint(m.EVAL_SEEDS))
        with self.assertRaises(ValueError):m.batch(3,1,1)
        with self.assertRaises(ValueError):m.train(m.model(1),'unknown',1,steps=2,batch_size=2)
    def test_independent_evaluation_marks_no_production_authority(self):
        r=m.evaluate(m.model(5),5,graphs=2)
        self.assertEqual(len(r),8)
        self.assertTrue(all(x['exact_reference_mae']<1e-5 and not x['production_authority'] for x in r))
if __name__=='__main__':unittest.main()
