# Точность конфигураций на задачах, похожих на управление CPU: чётность, мультиплексор, шахматная доска.
import torch,torch.nn as nn,torch.nn.functional as F,math,sys,json
torch.set_num_threads(2)
class L(nn.Module):
    def __init__(s,d,n,kind,act='relu',k=8):
        super().__init__();s.kind,s.act=kind,act
        s.W=nn.Parameter(torch.randn(n,d)/d**.5);s.b=nn.Parameter(torch.zeros(n))
        if kind=='conf':s.l=nn.Parameter(torch.zeros(n))
        if kind=='shared':s.P=nn.Parameter(torch.randn(k,d)/d**.5);s.Q=nn.Parameter(torch.randn(n,k)*.1)
        if kind in('low','feron'):s.A=nn.Parameter(torch.randn(n,2,d)/d**.5)
        if kind=='feron':
            s.c=nn.Parameter(torch.randn(n,d)*.3);s.p=nn.Parameter(torch.zeros(n));s.V=nn.Parameter(torch.randn(n,4,2)*.3);s.ph=nn.Parameter(torch.zeros(n,4));s.am=nn.Parameter(torch.zeros(n,4));s.lam=nn.Parameter(torch.zeros(n))
    def forward(s,x):
        f=x@s.W.T+s.b
        if s.kind=='conf':f=f+s.l*(x*x).sum(1,keepdim=True)
        if s.kind=='shared':f=f+(x@s.P.T).pow(2)@s.Q.T
        if s.kind=='low':f=f-torch.einsum('bd,nrd->bnr',x,s.A).pow(2).sum(2)
        if s.kind=='feron':
            dx=x[:,None]-s.c;z=torch.einsum('bnd,nrd->bnr',dx,s.A);e=(2+F.softplus(s.p))[None,:,None]
            nn_=((z.abs()+1e-4)**e).sum(2)**(1/e[:,:,0]);u=z/(nn_[...,None]+1e-4)
            rho=(s.am*torch.cos(torch.einsum('bnr,nmr->bnm',u,s.V)+s.ph)).sum(2);rad=nn_/rho.exp()
            lin=1+(dx*s.W).sum(2);l=torch.sigmoid(s.lam);return torch.sigmoid(4*(1-(l*rad+(1-l)*lin)))
        return {'relu':F.relu,'clip':lambda v:v.clamp(0,1),'sig':torch.sigmoid}[s.act](f)
def data(t,N=6000):
    if t=='parity8':
        x=torch.randint(0,2,(N,8)).float()*2-1;y=(x>0).sum(1)%2
    if t=='mux11':
        x=torch.randint(0,2,(N,11)).float()*2-1;a=((x[:,:3]>0).long()*torch.tensor([1,2,4])).sum(1);y=(x[:,3:].gather(1,a[:,None])[:,0]>0).long()
    if t=='board':
        x=torch.rand(N,2)*2-1;y=(((x+1)*2).floor().long().sum(1))%2
    return x,y
def run(t,kind,act,n,seed):
    torch.manual_seed(seed);x,y=data(t);xt,yt=x[5000:],y[5000:];x,y=x[:5000],y[:5000]
    m=nn.Sequential(L(x.shape[1],n,kind,act),nn.Linear(n,2));o=torch.optim.Adam(m.parameters(),3e-3)
    for e in range(60):
        for b in torch.randperm(5000).split(128):
            o.zero_grad();F.cross_entropy(m(x[b]),y[b]).backward();o.step()
    return (m(xt).argmax(1)==yt).float().mean().item()
cfg=[('MLP','mlp','relu'),('сфера+плоскость','conf','relu'),('оси relu','shared','relu'),('оси clip','shared','clip'),('оси sigmoid','shared','sig'),('эллипсоид r=2','low','relu'),('полный ферон','feron','relu')]
print(f"{'':18s}"+''.join(f"{t+' n='+str(n):>16s}" for t in('parity8','mux11','board') for n in(16,64)))
for nm,k,a in cfg:
    r=[]
    for t in('parity8','mux11','board'):
        for n in(16,64):
            r.append(sum(run(t,k,a,n,s) for s in range(3))/3)
    print(f"{nm:18s}"+''.join(f"{v*100:16.1f}" for v in r),flush=True)
