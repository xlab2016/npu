// Нейропроцессор. Здесь только железо: регистры кадров, память, порт, настоящие инструкции и вывод сети текущего навыка.
// Разбор текста, выражения, ошибки, циклы и выбор навыка выполняются навыками из файла модели.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <math.h>
#include <time.h>
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#undef NOP
#undef CONST
#undef RET
#undef AND
#undef OR
#undef XOR
#undef ADD
#undef SUB
#undef EQ
#undef LT
#undef BAD
#undef RAM
#undef CALL
#undef MOV
#undef TX
#undef RX
#undef THROW
#undef TRY
#undef LOAD
#undef STORE
#undef PLAN
#undef DEV
#undef OBS
#include <io.h>
#include <fcntl.h>
#define popen _popen
#define pclose _pclose
#define strcasecmp _stricmp
#define strncasecmp _strnicmp
#else
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/tcp.h>
#endif
enum{AND,OR,XOR,ADD,SUB,SHL,SHR,LT,EQ,LOAD,CONST,MOV,NOP,RET,STORE,RX,TX,CALL,TRY,THROW,BAD,PLAN,TXPLAN,RXNUM,ATOMS,UNARY,TXCOMBO,TXNEST,OBS,DEV,TXOP,TXS,TXF,NHW};
#define NR 16
#define DI 42
#define RAM 70000
#define BADV INT64_MIN
typedef struct{char name[17];int ar,nv,n,K,nx,nk,out;int64_t *k;float *W,*b,*P,*Q,*O,*c,*D;}Mod;
static Mod *M;static int NM;static int64_t ram[RAM];static uint64_t steps;
typedef struct{int m,pc,dst,catch_;uint64_t sdl;int64_t r[NR];}Fr;static Fr *st;
static float *rd(char**p,size_t n){float*a=malloc(n*4+64);memcpy(a,*p,n*4);*p+=n*4;return a;}
static uint64_t hname(const char*n){uint64_t h=0;for(;*n;n++)h=h*31+toupper(*n);return h;}
static void load(const char*f){FILE*h=fopen(f,"rb");if(!h){perror(f);exit(1);}fseek(h,0,SEEK_END);long l=ftell(h);rewind(h);char*b=malloc(l);if(fread(b,1,l,h)!=(size_t)l)exit(1);fclose(h);if(memcmp(b,"NPY2",4)){fprintf(stderr,"bad model\n");exit(1);}uint32_t*H=(void*)(b+4);NM=H[0];M=calloc(NM,sizeof(Mod));char*p=b+20;
 for(int i=0;i<NM;i++){Mod*m=&M[i];memcpy(m->name,p,16);p+=16;uint32_t u[3];memcpy(u,p,12);p+=12;m->ar=u[0];m->nv=u[1];uint32_t q[4];memcpy(q,p,16);p+=16;m->n=q[0];m->K=q[1];m->nx=q[2];m->nk=q[3];m->k=malloc(8*m->nk);memcpy(m->k,p,8*m->nk);p+=8*m->nk;int o=m->nv+NR*5+m->nk+m->nx;m->out=o;m->W=rd(&p,(size_t)m->n*DI);m->b=rd(&p,m->n);m->P=rd(&p,(size_t)m->K*DI);m->Q=rd(&p,(size_t)m->n*m->K);m->O=rd(&p,(size_t)o*m->n);m->c=rd(&p,o);m->D=rd(&p,(size_t)o*DI);
  ram[60001+3*i]=hname(m->name);ram[60002+3*i]=i;ram[60003+3*i]=m->ar;}ram[60000]=NM;}
static int fin=0,fout=1,is_sock=0;
static int io_read(void*b,int n){if(is_sock)return recv(fin,(char*)b,n,0);
#ifdef _WIN32
 return _read(fin,b,n);
#else
 return read(fin,b,n);
#endif
}
static int io_write(const void*b,int n){if(is_sock)return send(fout,(const char*)b,n,0);
#ifdef _WIN32
 return _write(fout,b,n);
#else
 return write(fout,b,n);
#endif
}
static unsigned char ib[1<<16];static int ii,in;static char ob[1<<16];static int ol;
static void flushz(void){int o=0;while(o<ol){int w=io_write(ob+o,ol-o);if(w<=0)exit(0);o+=w;}ol=0;}
static int rxb(void){if(ii>=in){flushz();in=io_read(ib,sizeof ib);ii=0;if(in<=0)return -1;}return ib[ii++];}
static void txb(int c){ob[ol++]=c;if(c=='\n'||ol>=(int)sizeof ob-64)flushz();}
static void txs(const char*s){for(;*s;s++)txb(*s);}
#include "plan2.h"
#include "device.h"
static inline int amax(const float*y,int n){int b=0;for(int i=1;i<n;i++)if(y[i]>y[b])b=i;return b;}
static void machine(int m){int sp=0;Fr*F=&st[0];memset(F,0,sizeof *F);F->m=m;uint64_t dl=~0ULL;float x[DI],z[32],y[2048],h[1024];
 for(;;){int thrown=0;steps++;Mod*Q=&M[F->m];for(int i=0;i<10;i++)x[i]=(F->pc>>i&1)*2-1;for(int i=0;i<NR;i++){x[10+i]=F->r[i]==0?1:-1;x[10+NR+i]=(int)(F->r[i]&1)*2-1;}
  for(int k=0;k<Q->K;k++){float s=0;const float*p=Q->P+k*DI;for(int j=0;j<DI;j++)s+=p[j]*x[j];z[k]=s*s;}
  for(int i=0;i<Q->n;i++){float s=Q->b[i];const float*w=Q->W+(size_t)i*DI;for(int j=0;j<DI;j++)s+=w[j]*x[j];const float*q=Q->Q+(size_t)i*Q->K;for(int k=0;k<Q->K;k++)s+=q[k]*z[k];h[i]=s>0?s:0;}
  for(int o=0;o<Q->out;o++){float s=Q->c[o];const float*d=Q->D+(size_t)o*DI;for(int j=0;j<DI;j++)s+=d[j]*x[j];const float*w=Q->O+(size_t)o*Q->n;for(int i=0;i<Q->n;i++)s+=w[i]*h[i];y[o]=s;}
  int o=0,op=amax(y,Q->nv);o+=Q->nv;int d=amax(y+o,NR);o+=NR;int A=amax(y+o,NR);o+=NR;int B=amax(y+o,NR);o+=NR;int C=amax(y+o,NR);o+=NR;int E=amax(y+o,NR);o+=NR;int K=amax(y+o,Q->nk);o+=Q->nk;int nx=amax(y+o,Q->nx);int64_t*r=F->r;
  int cm=-1,catching=0;int64_t aa=0,bb=0,cc=0;
  if(op>=NHW){cm=op-NHW;aa=r[A];bb=r[B];cc=r[C];}
  else switch(op){case AND:r[d]=r[A]&r[B];break;case OR:r[d]=r[A]|r[B];break;case XOR:r[d]=r[A]^r[B];break;case ADD:r[d]=(uint64_t)r[A]+r[B];break;case SUB:r[d]=(uint64_t)r[A]-r[B];break;case SHL:r[d]=(uint64_t)r[A]<<1;break;case SHR:r[d]=(uint64_t)r[A]>>1;break;case LT:r[d]=r[A]<r[B];break;case EQ:r[d]=r[A]==r[B];break;
  case LOAD:r[d]=ram[(uint64_t)r[A]%RAM];break;case CONST:r[d]=Q->k[K];break;case MOV:r[d]=r[A];break;case NOP:break;case STORE:ram[(uint64_t)r[A]%RAM]=r[B];break;
  case RX:{int c=rxb();if(c<0)return;r[d]=c;break;}case TX:txb(r[A]&255);r[d]=0;break;case BAD:r[d]=BADV;break;case PLAN:r[d]=plan(r[A]);break;case TXPLAN:txplan(r[A]);break;
  case CALL:if(r[A]<0||r[A]>=NM){thrown=1;break;}cm=r[A];aa=r[B];bb=r[C];cc=r[E];break;
  case TRY:cm=r[A];aa=r[B];bb=r[C];cc=r[E];catching=1;break;
  case THROW:thrown=1;break;
  case RXNUM:{int64_t c=ram[65000];uint64_t n=0;while(c>='0'&&c<='9'){n=n*10+(c-'0');c=rxb();if(c<0)return;}ram[65000]=c;r[d]=n;break;}
  case ATOMS:r[d]=atoms();break;case UNARY:r[d]=unary_k(r[A]);break;case TXCOMBO:txcombo(r[A],r[B],r[C]);break;case TXNEST:txnest(r[A],r[B]);break;
  case OBS:r[d]=dev_observe();break;case DEV:r[d]=dev_run(r[A]);break;case TXOP:txop(r[A],r[B]);break;case TXS:txmsg(r[A]);break;case TXF:txfacts(r[A]);break;
  case RET:{int64_t v=r[A];if(sp==0)return;if(F->catch_)dl=F->sdl;int dd=F->dst;F=&st[--sp];F->r[dd]=v;continue;}}
  if(steps>dl)thrown=1;
  if(cm>=0&&!thrown){if(sp>=(1<<14)-2){thrown=1;}else{F->pc=nx;Fr*G=&st[++sp];G->m=cm;G->pc=0;G->dst=d;G->catch_=catching;G->sdl=dl;memset(G->r,0,sizeof G->r);G->r[0]=aa;G->r[1]=bb;G->r[2]=cc;if(catching){uint64_t t=steps+(uint64_t)Q->k[K];if(t<dl)dl=t;}F=G;continue;}}
  if(thrown){while(sp>0&&!F->catch_)F=&st[--sp];if(sp==0)exit(1);dl=F->sdl;int dd=F->dst;F=&st[--sp];F->r[dd]=BADV;continue;}
  F->pc=nx;}}
int main(int c,char**v){const char*f="pyramid.bin",*pl="planner.bin";int port=0;for(int i=1;i<c;i++){if(!strcmp(v[i],"--tcp"))port=atoi(v[++i]);else if(!strcmp(v[i],"--planner"))pl=v[++i];else f=v[i];}st=malloc(sizeof(Fr)*(1<<14));load(f);load_plan(pl);load_update();
#ifdef _WIN32
 SetConsoleOutputCP(65001);_setmode(0,_O_BINARY);_setmode(1,_O_BINARY);{WSADATA w;WSAStartup(MAKEWORD(2,2),&w);}
#endif
 if(port){int s=socket(AF_INET,SOCK_STREAM,0),on=1;setsockopt(s,SOL_SOCKET,SO_REUSEADDR,(const char*)&on,sizeof on);struct sockaddr_in a;memset(&a,0,sizeof a);a.sin_family=AF_INET;a.sin_port=htons(port);a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);if(bind(s,(void*)&a,sizeof a)||listen(s,1))exit(1);fin=fout=accept(s,0,0);is_sock=1;setsockopt(fin,IPPROTO_TCP,TCP_NODELAY,(const char*)&on,sizeof on);}
 int m=-1;for(int i=0;i<NM;i++)if(!strcmp(M[i].name,"MAIN"))m=i;clock_t t0=clock();machine(m);flushz();double dt=(double)(clock()-t0)/CLOCKS_PER_SEC+1e-9;fprintf(stderr,"npu: навыков %d, шагов %llu, %.0f шагов/с\n",NM,(unsigned long long)steps,steps/dt);}
