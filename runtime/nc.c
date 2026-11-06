// neurocpu: регистры, память и порт здесь, а каждым тактом управляет сеть.
// В этом файле нет ни разбора команд, ни алгоритмов, ни таблицы микрокода.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <termios.h>
#include <signal.h>
#include <math.h>
#include <poll.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/tcp.h>

enum {NOP,MOV,LDI,ADD,SUB,SHL,SHR,NEG,CMP,INC,DEC,PUSH,POP,LD,ST,RX,SETC,GETC,TX,TXC,CALL,RET,RST,CALLR};
#define NREG 12
#define RAMW 8192
#define STK 65536
#define K_MAX 64
typedef struct {int n,d,k; float *W,*b,*P,*Q,*O;} Layer;
static int D,WB,K,NL,GEO; static float *b0,*O0; static Layer L[8];
static uint64_t R[NREG],ram[RAMW],st[STK]; static uint32_t cs[STK]; static int sp,csp,Z,Nf,C,pc,err_hw;
static uint64_t cycles; static double tNet;
// Фигуры памяти: выделяют подкуб состояний и задают управление. Учитель добавляет их мгновенно, без градиента.
typedef struct{uint64_t mask,val;uint32_t w;}Fig;
#define PCS 32768
static Fig *mem[PCS];static int memn[PCS],memc[PCS];static long nfig;
static long frozen_n,refused;static int memf[PCS];static inline int frozen_cnt(int p){return memf[p];}
static void add_fig(int p,uint64_t m,uint64_t v,uint32_t w){for(int i=0;i<memn[p]&&i<frozen_cnt(p);i++)if(mem[p][i].mask==m&&mem[p][i].val==v){refused++;return;}if(memn[p]==memc[p]){memc[p]=memc[p]?memc[p]*2:2;mem[p]=realloc(mem[p],sizeof(Fig)*memc[p]);}mem[p][memn[p]++]=(Fig){m,v,w};nfig++;}
typedef struct{char name[32];int ar;}Skill;static Skill sk[256];static int nsk;
static const char *sub_in;static char sub_out[256];static int sub_len,in_sub;
static int fdin=0,fdout=1; static char obuf[65536]; static int olen;
static float *xbuf,*fbuf,*ybuf,*hbuf;

static float *rd(FILE*f,size_t n){float*p;if(posix_memalign((void**)&p,64,n*sizeof(float)+64))exit(1);if(fread(p,sizeof(float),n,f)!=n){fprintf(stderr,"bad model\n");exit(1);}return p;}
static void load(const char*path){FILE*f=fopen(path,"rb");if(!f){perror(path);exit(1);}char m[4];uint32_t h[5];
 if(fread(m,1,4,f)!=4||memcmp(m,"NCP1",4)||fread(h,4,5,f)!=5){fprintf(stderr,"bad model\n");exit(1);}
 D=h[0];WB=h[1];K=h[2];NL=h[3];GEO=h[4];b0=rd(f,WB);O0=rd(f,WB*D);int mx=D;
 for(int i=0;i<NL;i++){uint32_t s[2];if(fread(s,4,2,f)!=2)exit(1);Layer*l=&L[i];l->n=s[0];l->d=s[1];l->k=K;
  l->W=rd(f,(size_t)l->n*l->d);l->b=rd(f,l->n);l->P=rd(f,(size_t)K*l->d);l->Q=rd(f,(size_t)l->n*K);l->O=rd(f,(size_t)WB*l->n);if(l->d+l->n>mx)mx=l->d+l->n;}
 fclose(f);posix_memalign((void**)&xbuf,64,(mx+64)*4);posix_memalign((void**)&fbuf,64,(mx+64)*4);posix_memalign((void**)&ybuf,64,(WB+64)*4);posix_memalign((void**)&hbuf,64,(mx+64)*4);}
// Отсечение по геометрии. Для каждого pc заранее считаем строгую верхнюю границу f нейрона по всем значениям
// остальных входов. Если граница меньше нуля, фигура не может содержать такое состояние и нейрон равен нулю.
// Результат совпадает с полным проходом, проверяется ключом --full.
static int *act_list[1024],act_n[1024];static float *Ot;static long act_total;static int FULL;
static void build_cull(void){Layer*l=&L[0];int n=l->n,d=l->d;float z_hi[K_MAX],z_lo[K_MAX];
 Ot=malloc(sizeof(float)*(size_t)n*WB);for(int i=0;i<n;i++)for(int b=0;b<WB;b++)Ot[(size_t)i*WB+b]=l->O[(size_t)b*n+i];
 int *tmp=malloc(sizeof(int)*n);
 for(int pc_=0;pc_<1024;pc_++){float xp[10];for(int j=0;j<10;j++)xp[j]=(pc_>>j&1)*2-1;
  for(int k=0;k<K;k++){const float*p=l->P+(size_t)k*d;double c=0,r=0;for(int j=0;j<10;j++)c+=p[j]*xp[j];for(int j=10;j<d;j++)r+=fabs(p[j]);
   double lo=c-r,hi=c+r,a=lo*lo,b=hi*hi;z_hi[k]=a>b?a:b;z_lo[k]=(lo<=0&&hi>=0)?0:(a<b?a:b);}
  int m=0;for(int i=0;i<n;i++){const float*w=l->W+(size_t)i*d,*q=l->Q+(size_t)i*K;double u=l->b[i];for(int j=0;j<10;j++)u+=w[j]*xp[j];for(int j=10;j<d;j++)u+=fabs(w[j]);
   for(int k=0;k<K;k++)u+=q[k]>0?q[k]*z_hi[k]:q[k]*z_lo[k];if(u>-1e-3)tmp[m++]=i;}
  act_n[pc_]=m;act_total+=m;act_list[pc_]=malloc(sizeof(int)*(m+1));memcpy(act_list[pc_],tmp,sizeof(int)*m);}
 free(tmp);}
static inline void flush_out(void){int o=0;while(o<olen){int w=write(fdout,obuf+o,olen-o);if(w<=0)exit(0);o+=w;}olen=0;}
static uint32_t infer(void){float *x=xbuf;
 for(int i=0;i<10;i++)x[i]=(pc>>i&1)*2-1;x[10]=Z*2-1;x[11]=Nf*2-1;for(int i=0;i<8;i++)x[12+i]=(C>>i&1)*2-1;
 for(int i=0;i<NREG;i++){x[20+i]=R[i]==0?1:-1;x[32+i]=(int)(R[i]&1)*2-1;}
 float *y=ybuf;for(int b=0;b<WB;b++){float s=b0[b];const float*o=O0+(size_t)b*D;for(int j=0;j<D;j++)s+=o[j]*x[j];y[b]=s;}
 float z[K_MAX];float *f=fbuf;static int on[1<<16];int non=0;
 {Layer*l=&L[0];int d=l->d,n=l->n;
  for(int k=0;k<K;k++){const float*p=l->P+(size_t)k*d;float s=0;for(int j=0;j<d;j++)s+=p[j]*x[j];z[k]=s*s;}
  int cnt=FULL?n:act_n[pc];const int*lst=act_list[pc];
  for(int ii=0;ii<cnt;ii++){int i=FULL?ii:lst[ii];const float*w=l->W+(size_t)i*d;float s=l->b[i];for(int j=0;j<d;j++)s+=w[j]*x[j];
   const float*q=l->Q+(size_t)i*K;for(int k=0;k<K;k++)s+=q[k]*z[k];
   if(s>0){f[non]=s;on[non++]=i;const float*o=Ot+(size_t)i*WB;for(int b=0;b<WB;b++)y[b]+=s*o[b];}}}
 for(int li=1;li<NL;li++){Layer*l=&L[li],*pv=&L[li-1];int d=l->d,n=l->n;float g[4096];float zz[K_MAX];
  if(li==1){for(int k=0;k<K;k++){const float*p=l->P+(size_t)k*d;float s=0;for(int j=0;j<D;j++)s+=p[j]*x[j];for(int t=0;t<non;t++)s+=p[D+on[t]]*f[t];zz[k]=s*s;}
   for(int i=0;i<n;i++){const float*w=l->W+(size_t)i*d;float s=l->b[i];for(int j=0;j<D;j++)s+=w[j]*x[j];for(int t=0;t<non;t++)s+=w[D+on[t]]*f[t];const float*q=l->Q+(size_t)i*K;for(int k=0;k<K;k++)s+=q[k]*zz[k];g[i]=s>0?s:0;}}
  else{memcpy(x+D,f,pv->n*sizeof(float));
   for(int k=0;k<K;k++){const float*p=l->P+(size_t)k*d;float s=0;for(int j=0;j<d;j++)s+=p[j]*x[j];zz[k]=s*s;}
   for(int i=0;i<n;i++){const float*w=l->W+(size_t)i*d;float s=l->b[i];for(int j=0;j<d;j++)s+=w[j]*x[j];const float*q=l->Q+(size_t)i*K;for(int k=0;k<K;k++)s+=q[k]*zz[k];g[i]=s>0?s:0;}}
  for(int b=0;b<WB;b++){const float*o=l->O+(size_t)b*n;float s=0;for(int j=0;j<n;j++)s+=o[j]*g[j];y[b]+=s;}
  memcpy(f,g,n*sizeof(float));}
 uint32_t w=0;for(int b=0;b<WB;b++)if(y[b]>0)w|=1u<<b;return w;}
static int rawrx(void){static unsigned char b[65536];static int n,i;if(i>=n){flush_out();n=read(fdin,b,sizeof b);i=0;if(n<=0)return -1;}return b[i++];}
static void portline(char*l);
static char pend[1<<21];static int pi_,pn_;static int portfilter(char*l,char*out);
static int rx(void){if(in_sub)return *sub_in?(unsigned char)*sub_in++:-1;
 for(;;){if(pi_<pn_)return (unsigned char)pend[pi_++];static char l[1<<20];int k=0,c;while((c=rawrx())>=0&&c!='\n'&&k<(1<<20)-4)l[k++]=c;if(c<0&&k==0)return -1;l[k]=0;
  if(l[0]=='@'||l[0]=='?'){portline(l);continue;}pn_=portfilter(l,pend);pi_=0;if(pn_<0){pn_=0;continue;}}}
static void tx(int c){if(in_sub){if(sub_len<255)sub_out[sub_len++]=c;return;}obuf[olen++]=c;if(c=='\n'||olen>=(int)sizeof obuf-1)flush_out();}
static void reset(void){memset(R,0,sizeof R);sp=csp=Z=Nf=C=pc=0;}
static void setf(uint64_t v){Z=v==0;Nf=v>>63;}
static int machine(uint64_t limit){for(;;){
  uint32_t w=0;int hit=0;if(memn[pc]){uint64_t f=(uint64_t)Z|(uint64_t)Nf<<1|(uint64_t)C<<2;for(int i=0;i<NREG;i++){f|=(uint64_t)(R[i]==0)<<(10+i);f|=(R[i]&1)<<(22+i);}
   int fb=-1;for(int i=0;i<memn[pc];i++){if(!mem[pc][i].mask){fb=i;continue;}if((f&mem[pc][i].mask)==mem[pc][i].val){w=mem[pc][i].w;hit=1;break;}}if(!hit&&fb>=0){w=mem[pc][fb].w;hit=1;}}
  if(!hit){if(pc>=1024){err_hw=1;return 2;}w=infer();}
  int op=w&31,a=w>>5&15,b=w>>9&255,nx=w>>17&32767,b4=b&15;if(a>=NREG)a=NREG-1;if(b4>=NREG)b4=NREG-1;
  switch(op){case NOP:break;case MOV:R[a]=R[b4];setf(R[a]);break;case LDI:R[a]=b;break;
  case ADD:R[a]+=R[b4];setf(R[a]);break;case SUB:R[a]-=R[b4];setf(R[a]);break;case SHL:R[a]<<=1;setf(R[a]);break;case SHR:R[a]>>=1;setf(R[a]);break;
  case NEG:R[a]=-R[a];setf(R[a]);break;case CMP:Z=R[a]==R[b4];Nf=(int64_t)R[a]<(int64_t)R[b4];break;
  case INC:R[a]++;setf(R[a]);break;case DEC:R[a]--;setf(R[a]);break;
  case PUSH:if(sp<STK)st[sp++]=R[a];break;case POP:R[a]=sp?st[--sp]:0;break;
  case LD:R[a]=ram[R[b4]%RAMW];break;case ST:ram[R[a]%RAMW]=R[b4];break;
  case RX:{int c=rx();if(c<0)return 0;C=c;break;}case SETC:C=R[a]&255;break;case GETC:R[a]=C;break;
  case TX:tx(R[a]&255);break;case TXC:tx(b);break;
  case CALL:if(csp<STK)cs[csp++]=pc+1;break;case RET:nx=csp?cs[--csp]:0;break;case RST:sp=csp=0;break;case CALLR:if(csp<STK)cs[csp++]=pc+1;nx=R[a]&32767;break;default:break;}
  pc=nx;cycles++;if(limit&&cycles>=limit)return 1;}}
#include "work.h"
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+1e-9*t.tv_nsec;}
static void serve_tcp(int port){int s=socket(AF_INET,SOCK_STREAM,0),on=1;setsockopt(s,SOL_SOCKET,SO_REUSEADDR,&on,sizeof on);
 struct sockaddr_in a={0};a.sin_family=AF_INET;a.sin_port=htons(port);a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 if(bind(s,(void*)&a,sizeof a)||listen(s,1)){perror("port");exit(1);}fprintf(stderr,"nc: порт TCP 127.0.0.1:%d\n",port);
 for(;;){int c=accept(s,0,0);if(c<0)continue;setsockopt(c,IPPROTO_TCP,TCP_NODELAY,&on,sizeof on);fdin=fdout=c;reset();machine(0);close(c);exit(0);}}
int main(int ac,char**av){const char*model="models/nc2.bin",*ser=0,*memfile=0,*plan=0;int noexp_=0;int tcp=0,pty=0;
 for(int i=1;i<ac;i++){if(!strcmp(av[i],"--model"))model=av[++i];else if(!strcmp(av[i],"--mem"))memfile=av[++i];else if(!strcmp(av[i],"--planner"))plan=av[++i];else if(!strcmp(av[i],"--noexp"))noexp_=1;else if(!strcmp(av[i],"--tcp"))tcp=atoi(av[++i]);else if(!strcmp(av[i],"--serial"))ser=av[++i];else if(!strcmp(av[i],"--pty"))pty=1;else if(!strcmp(av[i],"--full"))FULL=1;else{fprintf(stderr,"nc [--model файл] [--mem файл] [--tcp порт | --serial /dev/ttyX | --pty]\n");return 1;}}
 load(model);int tot=0;for(int i=0;i<NL;i++)tot+=L[i].n;build_cull();if(memfile)load_mem(memfile);else seed_skills();if(plan)load_plan(plan);noexp=noexp_;fprintf(stderr,"nc: сеть %d нейронов, %d слоёв, в среднем на строку микрокода считается %.1f нейронов первого слоя из %d\n",tot,NL,act_total/1024.0,L[0].n);
 if(tcp){serve_tcp(tcp);}
 if(pty||ser){int f;if(pty){f=posix_openpt(O_RDWR|O_NOCTTY);grantpt(f);unlockpt(f);fprintf(stderr,"nc: виртуальный порт %s\n",ptsname(f));}else{f=open(ser,O_RDWR|O_NOCTTY);if(f<0){perror(ser);return 1;}}
  struct termios t;if(!tcgetattr(f,&t)){cfmakeraw(&t);if(ser){cfsetspeed(&t,B115200);}tcsetattr(f,TCSANOW,&t);}fdin=fdout=f;}
 double t0=now();reset();machine(0);flush_out();double dt=now()-t0;fprintf(stderr,"nc: тактов %llu, %.0f тактов/с\n",(unsigned long long)cycles,cycles/dt);return 0;}
