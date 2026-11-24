import json, unittest, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_native_ollama_v33 as m
D='a'*64
MODEL='qwen3:1.7b'
class NativeTests(unittest.TestCase):
    def test_pins_artifact_and_returns_unmodified_integer(self):
        tags={'models':[{'name':MODEL,'digest':D}]}
        reply={'model':MODEL,'done':True,'done_reason':'stop','eval_count':3,'message':{'content':' 41 '}}
        with patch.object(m,'_json_request',side_effect=[(tags,b'tags'),(reply,b'raw-response'),(tags,b'tags')]) as call:
            v=m.native_request(11434,MODEL,'17+24','unused',32,10,digest=D)
        self.assertEqual(v,(' 41 ',3,m.hashlib.sha256(b'raw-response').hexdigest()))
        body=call.call_args_list[1].args[3]
        self.assertEqual(body['format'],{'type':'integer'})
        self.assertIs(body['think'],False)
        self.assertEqual(body['options']['num_thread'],2)
    def test_digest_mismatch_blocks_before_generation(self):
        with patch.object(m,'_json_request',return_value=({'models':[{'name':MODEL,'digest':'b'*64}]},b'x')) as call:
            with self.assertRaises(ValueError):m.native_request(11434,MODEL,'1+1','unused',32,10,digest=D)
        self.assertEqual(call.call_count,1)
    def test_changed_digest_after_generation_rejected(self):
        tags={'models':[{'name':MODEL,'digest':D}]}
        changed={'models':[{'name':MODEL,'digest':'b'*64}]}
        reply={'model':MODEL,'done':True,'done_reason':'stop','eval_count':3,'message':{'content':'2'}}
        with patch.object(m,'_json_request',side_effect=[(tags,b'x'),(reply,b'x'),(changed,b'x')]):
            with self.assertRaises(ValueError):m.native_request(11434,MODEL,'1+1','unused',32,10,digest=D)
    def test_invalid_native_output_refused(self):
        tags={'models':[{'name':MODEL,'digest':D}]}
        for changes in [{'done':False},{'eval_count':33},{'model':'other'},{'message':{'content':'{}'}},{'done_reason':'length'}]:
            reply={'model':MODEL,'done':True,'done_reason':'stop','eval_count':3,'message':{'content':'2'},**changes}
            with patch.object(m,'_json_request',side_effect=[(tags,b'x'),(reply,b'x')]):
                with self.assertRaises(ValueError):m.native_request(11434,MODEL,'1+1','unused',32,10,digest=D)
    def test_no_secret_bearing_or_unbounded_input(self):
        for port,prompt,cap,timeout,digest in [(0,'1',32,10,D),(11434,'x'*513,32,10,D),(11434,'1',65,10,D),(11434,'1',32,61,D),(11434,'1',32,10,'not-a-digest')]:
            with patch.object(m,'_json_request') as call:
                with self.assertRaises(ValueError):m.native_request(port,MODEL,prompt,'unused',cap,timeout,digest=digest)
                call.assert_not_called()
if __name__=='__main__':unittest.main()
