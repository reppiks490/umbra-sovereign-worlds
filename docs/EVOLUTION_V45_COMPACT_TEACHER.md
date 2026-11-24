# MYRIAD v4.5 compact teacher protocol
Teacher output is a strict array of twelve binary labels. Each label binds to the
same ordered, seeded case, with no answer key supplied to the model. The original
output and its deterministic normalization are both stored, HMAC sealed and replayed
before student training. Incorrect labels are excluded. The compact protocol reduces
completion length and uses a 1024-token context. DeepSeek uses its own native thinking
behavior rather than forcing an unsupported toggle. The model may still fail to produce
valid output within budget; failures are recorded and count toward least-attempted
small-teacher rotation. No failed output becomes training data.
Both full and compressed Qwen3 8B teachers retain their respective memory and
exclusive-residency gates. No inference is claimed until a valid receipt exists.
The existing v4.4 scheduler invokes this protocol in its teacher windows.
