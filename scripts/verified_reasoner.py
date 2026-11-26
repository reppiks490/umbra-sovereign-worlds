"""Bounded exact-arithmetic execution and replay for research agents.

No Python eval, executable code, network, filesystem, trading or weight updates.
A valid program proves computation, not that its premises or interpretation are true.
"""
import argparse, hashlib, json, re
from fractions import Fraction

class ReasoningError(ValueError):
    pass

NUMBER=re.compile(r'[+-]?[0-9]{1,24}(?:\.[0-9]{1,24})?')
IDENT=re.compile(r'[a-zA-Z][a-zA-Z0-9_]{0,31}')
MAX_BITS=256
ARITY={'add':(2,16),'sub':(2,2),'mul':(2,16),'div':(2,2),'neg':(1,1),
       'abs':(1,1),'mean':(1,16),'min':(1,16),'max':(1,16),
       'return_pct':(2,2),'percent_of':(2,2),'pow':(2,2)}

def bounded(v):
    if v.numerator.bit_length()>MAX_BITS or v.denominator.bit_length()>MAX_BITS:
        raise ReasoningError('numeric budget exceeded')
    return v

def literal(s):
    if not isinstance(s,str) or not NUMBER.fullmatch(s):
        raise ReasoningError('invalid literal')
    return bounded(Fraction(s))

def operation(op, a):
    if op not in ARITY or not ARITY[op][0]<=len(a)<=ARITY[op][1]:
        raise ReasoningError('operation arity')
    try:
        if op=='add':v=sum(a,Fraction(0))
        elif op=='sub':v=a[0]-a[1]
        elif op=='mul':
            v=Fraction(1)
            for x in a:v=bounded(v*x)
        elif op=='div':v=a[0]/a[1]
        elif op=='neg':v=-a[0]
        elif op=='abs':v=abs(a[0])
        elif op=='mean':v=sum(a,Fraction(0))/len(a)
        elif op=='min':v=min(a)
        elif op=='max':v=max(a)
        elif op=='return_pct':v=(a[1]/a[0]-1)*100
        elif op=='percent_of':v=a[0]*a[1]/100
        elif op=='pow':
            if a[1].denominator!=1 or abs(a[1])>16:raise ReasoningError('exponent budget')
            v=a[0]**int(a[1])
        return bounded(v)
    except ZeroDivisionError as e:raise ReasoningError('zero denominator') from e

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def execute_plan(plan):
    if not isinstance(plan,dict) or set(plan)!= {'nodes','output'}:
        raise ReasoningError('plan schema')
    nodes=plan['nodes'];output=plan['output']
    if not isinstance(nodes,list) or not 1<=len(nodes)<=128 or not isinstance(output,str):
        raise ReasoningError('plan size')
    values={};deps={};trace=[]
    for node in nodes:
        if not isinstance(node,dict):raise ReasoningError('node schema')
        ident,op=node.get('id'),node.get('op')
        if not isinstance(ident,str) or not IDENT.fullmatch(ident) or ident in values or not isinstance(op,str):
            raise ReasoningError('node identity')
        if op=='literal':
            if set(node)!= {'id','op','value'}:raise ReasoningError('literal schema')
            args=[];v=literal(node['value'])
        else:
            if set(node)!= {'id','op','args'} or op not in ARITY:raise ReasoningError('operation schema')
            args=node['args']
            if not isinstance(args,list) or not ARITY[op][0]<=len(args)<=ARITY[op][1] or any(not isinstance(x,str) or x not in values for x in args):
                raise ReasoningError('forward or absent dependency')
            v=operation(op,[values[x] for x in args])
        values[ident]=v;deps[ident]=args
        trace.append({'id':ident,'op':op,'dependencies':args.copy(),'value':str(v)})
    if output not in values:raise ReasoningError('unknown output')
    reachable=set();stack=[output]
    while stack:
        k=stack.pop()
        if k not in reachable:
            reachable.add(k);stack.extend(deps[k])
    if reachable!=set(values):raise ReasoningError('unreachable nodes')
    return {'schema':'exact-rational-plan-v1','plan_sha256':digest(plan),
            'value':str(values[output]),'trace':trace,'trace_sha256':digest(trace),
            'production_authority':False,'scope':'computation only; premises not independently established'}

def verify_receipt(plan,receipt):
    try:return execute_plan(plan)==receipt
    except (ReasoningError,TypeError,ValueError):return False

TOKEN=re.compile(r'[0-9]+(?:\.[0-9]+)?|[()+*/-]')
def calculate(expr):
    """Compile an explicitly scoped expression; reject natural-language ambiguity."""
    if not isinstance(expr,str) or not 1<=len(expr)<=512:raise ReasoningError('expression budget')
    s=expr.replace('×','*').replace('÷','/').replace('x','*').replace('X','*')
    tokens=[];i=0
    while i<len(s):
        if s[i] in ' \t':i+=1;continue
        m=TOKEN.match(s,i)
        if not m:raise ReasoningError('invalid expression token')
        t=m.group()
        # Numeric adjacency before an opening parenthesis only.
        if t=='(' and tokens and NUMBER.fullmatch(tokens[-1]):tokens.append('*')
        tokens.append(t);i=m.end()
        if len(tokens)>256:raise ReasoningError('token budget')
    pos=0;nodes=[]
    def node(op,**fields):
        ident='n'+str(len(nodes));nodes.append({'id':ident,'op':op,**fields})
        if len(nodes)>128:raise ReasoningError('node budget')
        return ident
    def take():
        nonlocal pos
        if pos>=len(tokens):raise ReasoningError('unexpected end')
        t=tokens[pos];pos+=1;return t
    def peek():return tokens[pos] if pos<len(tokens) else None
    def factor(depth):
        if depth>24:raise ReasoningError('nesting budget')
        t=take()
        if t=='(':
            v=expression(0,depth+1)
            if take()!=')':raise ReasoningError('unbalanced parentheses')
            return v
        if t in ('+','-'):
            v=factor(depth+1)
            return node('neg',args=[v]) if t=='-' else v
        literal(t)
        return node('literal',value=t)
    precedence={'+':1,'-':1,'*':2,'/':2}
    ops={'+':'add','-':'sub','*':'mul','/':'div'}
    def expression(minimum,depth):
        left=factor(depth)
        while peek() in precedence and precedence[peek()]>=minimum:
            t=take();right=expression(precedence[t]+1,depth+1)
            left=node(ops[t],args=[left,right])
        return left
    output=expression(0,0)
    if pos!=len(tokens):raise ReasoningError('unexpected trailing token')
    plan={'nodes':nodes,'output':output}
    return {**execute_plan(plan),'plan':plan}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('expression');a=p.parse_args()
    print(json.dumps(calculate(a.expression)))
