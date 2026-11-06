// Перебор программ по примерам. Форма: pre*; [while cond { body+ }; post*]. Цена токенов задаётся извне.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
enum{G_NONE,G_ODD,G_EVEN,G_ZERO,G_NZ,G_LT,G_GE,NG};
enum{O_MOV,O_ADD,O_SUB,O_SWAP,O_SHL,O_SHR,O_INC,O_DEC,O_ZERO,O_TEN,NBASE};
#define MAXSK 40
#define NOPS (NBASE+MAXSK)
#define MAXS 8
typedef struct{int g,gx,gy,op,a,b;}St;
typedef struct{int np,nb,nq,lg,lx,ly;St p[MAXS],b[MAXS],q[MAXS];}Prog;
static Prog lib[MAXSK];static int nlib,lar[MAXSK];
static inline int tst(int g,int x,int y,const int64_t*r){switch(g){case G_ODD:return r[x]&1;case G_EVEN:return !(r[x]&1);case G_ZERO:return r[x]==0;case G_NZ:return r[x]!=0;case G_LT:return r[x]<r[y];case G_GE:return r[x]>=r[y];}return 1;}
static int run(const Prog*P,int64_t*r,long*steps);
static inline int exs(const St*s,int64_t*r,long*steps){if(--*steps<0)return 0;if(s->g&&!tst(s->g,s->gx,s->gy,r))return 1;int a=s->a,b=s->b;int64_t t;
 switch(s->op){case O_MOV:r[a]=r[b];break;case O_ADD:r[a]=(int64_t)((uint64_t)r[a]+(uint64_t)r[b]);break;case O_SUB:r[a]=(int64_t)((uint64_t)r[a]-(uint64_t)r[b]);break;case O_SWAP:t=r[a];r[a]=r[b];r[b]=t;break;
 case O_SHL:r[a]=(int64_t)((uint64_t)r[a]<<1);break;case O_SHR:r[a]=(int64_t)((uint64_t)r[a]>>1);break;case O_INC:r[a]=(int64_t)((uint64_t)r[a]+1);break;case O_DEC:r[a]=(int64_t)((uint64_t)r[a]-1);break;case O_ZERO:r[a]=0;break;case O_TEN:r[a]=10;break;
 default:{int k=s->op-NBASE;int64_t q[4]={r[a],lar[k]==2?r[b]:0,0,0};if(!run(&lib[k],q,steps))return 0;r[a]=q[3];}}return 1;}
static int run(const Prog*P,int64_t*r,long*steps){for(int i=0;i<P->np;i++)if(!exs(&P->p[i],r,steps))return 0;
 if(P->lg){while(tst(P->lg,P->lx,P->ly,r)){if(--*steps<0)return 0;for(int i=0;i<P->nb;i++)if(!exs(&P->b[i],r,steps))return 0;}for(int i=0;i<P->nq;i++)if(!exs(&P->q[i],r,steps))return 0;}return 1;}
// ---- API
void lib_reset(void){nlib=0;}
int lib_add(const Prog*p,int ar){lib[nlib]=*p;lar[nlib]=ar;return nlib++;}
int prog_size(void){return sizeof(Prog);}
int run_one(const Prog*p,int64_t a,int64_t b,int64_t c,long lim,int64_t*out){int64_t r[4]={a,b,c,0};long s=lim;int ok=run(p,r,&s);*out=r[3];return ok;}
typedef struct{St s;double c;}CS;
static CS *ST;static int NST;static double wg[NG],wo[NOPS],wl[NG+1];
static int cmpc(const void*a,const void*b){double d=((CS*)a)->c-((CS*)b)->c;return d<0?-1:d>0;}
static void build(void){int cap=200000;if(!ST)ST=malloc(sizeof(CS)*cap);NST=0;
 for(int g=0;g<NG;g++){int nx=g==G_NONE?1:4,ny=(g==G_LT||g==G_GE)?4:1;for(int x=0;x<nx;x++)for(int y=0;y<ny;y++){if(ny>1&&x==y)continue;double gc=wg[g]+(g?2:0)+(ny>1?2:0);
  for(int o=0;o<NBASE+nlib;o++){int two=(o<=O_SWAP)||(o>=NBASE&&lar[o-NBASE]==2);for(int a=0;a<4;a++)for(int b=0;b<(two?4:1);b++){
   if(o<=O_SWAP&&a==b)continue;if(o==O_SWAP&&a>b)continue;
   CS c;c.s=(St){g,x,y,o,a,b};c.c=gc+wo[o]+2+(two?2:0);ST[NST++]=c;}}}}
 qsort(ST,NST,sizeof(CS),cmpc);}
static const int64_t *EX;static int NE;static long LIM,LIM0;static Prog cur,found;static int got;static uint64_t cand,maxc;static double lo,hi;
static inline int evalp(void){cand++;if(cand>=maxc)return -1;
 if(cur.lg){int w=0;for(int i=0;i<cur.nb;i++){int o=cur.b[i].op;if(o==O_SWAP?(cur.b[i].a==cur.lx||cur.b[i].b==cur.lx||cur.b[i].a==cur.ly||cur.b[i].b==cur.ly):(cur.b[i].a==cur.lx||cur.b[i].a==cur.ly))w=1;}if(!w)return 0;}
 int w3=0;for(int i=0;i<cur.np;i++)w3|=cur.p[i].a==3||(cur.p[i].op==O_SWAP&&cur.p[i].b==3);if(cur.lg){for(int i=0;i<cur.nb;i++)w3|=cur.b[i].a==3||(cur.b[i].op==O_SWAP&&cur.b[i].b==3);for(int i=0;i<cur.nq;i++)w3|=cur.q[i].a==3||(cur.q[i].op==O_SWAP&&cur.q[i].b==3);}if(!w3)return 0;
 for(int e=0;e<NE;e++){const int64_t*x=EX+e*4;int64_t r[4]={x[0],x[1],x[2],0};long s=e<2?LIM0:LIM;if(!run(&cur,r,&s)||r[3]!=x[3])return 0;}
 found=cur;got=1;return 1;}
static int rec(int sec,double c){int rr;
 if(sec==0){if(c>lo&&c<=hi&&cur.np){cur.lg=0;rr=evalp();if(rr)return rr;}
  if(cur.np<5)for(int i=0;i<NST;i++){double d=c+ST[i].c+1;if(d>hi)break;cur.p[cur.np++]=ST[i].s;rr=rec(0,d);cur.np--;if(rr)return rr;}
  for(int g=G_ODD;g<NG;g++){int nx=4,ny=(g==G_LT||g==G_GE)?4:1;for(int x=0;x<nx;x++)for(int y=0;y<ny;y++){if(ny>1&&x==y)continue;double d=c+wl[g]+2+(ny>1?2:0);if(d>hi)continue;cur.lg=g;cur.lx=x;cur.ly=y;cur.nb=cur.nq=0;rr=rec(1,d);if(rr)return rr;}}
  cur.lg=0;return 0;}
 if(sec==1){if(cur.nb<5)for(int i=0;i<NST;i++){double d=c+ST[i].c+1;if(d>hi)break;cur.b[cur.nb++]=ST[i].s;rr=rec(1,d);if(!rr&&cur.nb>0)rr=rec(2,d);cur.nb--;if(rr)return rr;}return 0;}
 if(c>lo&&c<=hi){rr=evalp();if(rr)return rr;}
 if(cur.nq<2)for(int i=0;i<NST;i++){double d=c+ST[i].c+1;if(d>hi)break;cur.q[cur.nq++]=ST[i].s;rr=rec(2,d);cur.nq--;if(rr)return rr;}
 return 0;}
// веса: биты на токен; ex: NE*4 (a,b,c,ответ). Возврат 1 найдено, 0 предел
int search(const double*g,const double*o,const double*l,const int64_t*ex,int ne,long lim,long lim0,uint64_t maxcand,Prog*out,uint64_t*used,double*bits){
 memcpy(wg,g,sizeof(double)*NG);memcpy(wo,o,sizeof(double)*(NBASE+nlib));memcpy(wl,l,sizeof(double)*NG);build();EX=ex;NE=ne;LIM=lim;LIM0=lim0;maxc=maxcand;cand=0;got=0;
 double b=8;lo=-1;for(;b<90;b+=2){hi=b;memset(&cur,0,sizeof cur);int r=rec(0,0);if(r==1){*out=found;*used=cand;*bits=b;return 1;}if(r<0)break;lo=hi;}
 *used=cand;*bits=b;return 0;}
// случайные программы для обучения: токены-метки и выходы на пробах
static uint64_t rs=88172645463325252ULL;static inline uint32_t rnd(uint32_t n){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return (rs>>11)%n;}
static St rst(int nops){St s;memset(&s,0,sizeof s);s.g=rnd(3)==0?1+rnd(NG-1):0;s.gx=rnd(4);s.gy=(s.gx+1+rnd(3))%4;do{s.op=rnd(NBASE+nops);s.a=rnd(4);s.b=rnd(4);}while(s.op<=O_SWAP&&s.a==s.b);return s;}
void rseed(uint64_t s){rs=s*2654435761ULL+88172645463325252ULL;}
void dream(Prog*p){memset(p,0,sizeof *p);p->np=rnd(3);for(int i=0;i<p->np;i++)p->p[i]=rst(nlib);if(rnd(10)<8){p->lg=1+rnd(NG-1);p->lx=rnd(4);p->ly=(p->lx+1+rnd(3))%4;p->nb=1+rnd(4);for(int i=0;i<p->nb;i++)p->b[i]=rst(nlib);p->nq=rnd(4)==0;for(int i=0;i<p->nq;i++)p->q[i]=rst(nlib);if(rnd(2))p->q[p->nq?0:0]=(St){0,0,0,O_MOV,3,rnd(3)},p->nq=1;}else if(p->np==0){p->np=1;p->p[0]=rst(nlib);}
 if(rnd(2)){}}

// пакет случайных программ: выходы на пробах px/py, 1<<62 означает «нет ответа»
void dream_batch(int n,Prog*ps,int64_t*out,const int64_t*px,const int64_t*py,int np){for(int i=0;i<n;i++){dream(&ps[i]);int un=i%3==0;int fl=0;for(int k=0;k<np;k++){out[(size_t)i*np+k]=1LL<<62;}for(int k=0;k<np&&fl<8;k++){int64_t r[4]={px[k],un?0:py[k],0,0};long s=2000;int ok=run(&ps[i],r,&s);fl+=!ok;if(!ok||r[3]>=(1LL<<62)||r[3]<=-(1LL<<62))r[3]=1LL<<62;out[(size_t)i*np+k]=r[3];}}}
