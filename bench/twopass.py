# Два прохода с рёбрами против одного прохода при равном числе нейронов. Рёбра садятся на трудные примеры на середине обучения.
import torch,torch.nn.functional as F,sys
torch.set_num_threads(1)
K=8
class G:
    def __init__(s,d,n,two,cls=2):
        s.two=two;s.W=(torch.randn(n,d)/d**.5).requires_grad_();s.b=torch.zeros(n).requires_grad_();s.P=(torch.randn(K,d)/d**.5).requires_grad_();s.Q=(torch.randn(n,K)*.1).requires_grad_();s.O=(torch.randn(cls,n)*.1).requires_grad_();s.c=torch.zeros(cls).requires_grad_();s.m=None;s.d=d;s.n=n
    def ps(s):return [s.W,s.b,s.P,s.Q,s.O,s.c]+([s.H,s.th,s.C] if s.m is not None else [])
    def fig(s,x):return F.relu(x@s.W.T+s.b+(x@s.P.T).pow(2)@s.Q.T)
    def __call__(s,x):
        a=s.fig(x)
        if s.m is None:return a@s.O.T+s.c
        return s.fig(x+F.relu(a@(s.H*s.m)-s.th)@s.C)@s.O.T+s.c
    def edges(s,x,y,e):
        with torch.no_grad():
            i=F.cross_entropy(s(x),y,reduction='none').topk(e).indices;a=s.fig(x[i]);t=a.topk(3,1);M=torch.zeros(s.n,e)
            for j in range(e):M[t.indices[j],j]=1
            s.m=M;s.H=M.clone().requires_grad_();s.th=(a.gather(1,t.indices).sum(1)*.6).requires_grad_();s.C=torch.zeros(e,s.d).requires_grad_()
def data(t,N=6000):
    if t=='parity8':x=torch.randint(0,2,(N,8)).float()*2-1;y=(x>0).sum(1)%2
    if t=='mux11':x=torch.randint(0,2,(N,11)).float()*2-1;a=((x[:,:3]>0).long()*torch.tensor([1,2,4])).sum(1);y=(x[:,3:].gather(1,a[:,None])[:,0]>0).long()
    if t=='board':x=torch.rand(N,2)*2-1;y=(((x+1)*2).floor().long().sum(1))%2
    if t=='context':   # правило меняется от контекста: две координаты выбирают, какая из 4 шахматных досок действует
        x=torch.rand(N,6)*2-1;c=(x[:,0]>0).long()+2*(x[:,1]>0).long();p=x[torch.arange(N),2+c];q=x[torch.arange(N),2+(c+1)%4];y=(((p*2).floor().long()+(q*2).floor().long())%2)
    return x,y
def run(t,two,n,seed):
    torch.manual_seed(seed);x,y=data(t);xt,yt=x[5000:],y[5000:];x,y=x[:5000],y[:5000];g=G(x.shape[1],n,two)
    for ph in range(2):
        o=torch.optim.Adam(g.ps(),3e-3)
        for e in range(40):
            for b in torch.randperm(5000).split(128):o.zero_grad();F.cross_entropy(g(x[b]),y[b]).backward();o.step()
        if ph==0 and two:g.edges(x,y,n)
    return (g(xt).argmax(1)==yt).float().mean().item()
print(f"{'':10s}{'n':>4s}{'один проход':>14s}{'два прохода':>14s}")
for t in('parity8','mux11','board','context'):
    for n in(16,48):
        a=[run(t,0,n,s) for s in range(4)];b=[run(t,1,n,s) for s in range(4)]
        print(f"{t:10s}{n:4d}{sum(a)/4*100:10.1f}±{(max(a)-min(a))*50:.1f}{sum(b)/4*100:10.1f}±{(max(b)-min(b))*50:.1f}",flush=True)
