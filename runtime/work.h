// Порт учителя (@) и режим работы без названия навыка (?).
// @F pc mask val word  новая фигура памяти     @S имя арность  новый навык
// @SAVE файл           сохранить               @END            подтверждение
// ? a b = r; a b = r; x y    задача по примерам    ?SEQ v1 v2 v3 ...  продолжить ряд
#include <ctype.h>
#include <strings.h>
#include <inttypes.h>
static void pout(const char*t){for(;*t;t++)tx(*t);}
// Составные навыки: DEF переводит формулу в новые строки поверх замороженных навыков. Старые веса и фигуры не меняются.
typedef struct{char name[32],par[3][16],body[1024];int ar,code,entry,h,islist;}Comp;static Comp cp[256];static int ncp;
typedef struct{char name[32];int code,h,entry;}Known;static Known kn[256];static int nkn;
static int lb_disp,lb_mul,lb_div,lb_pow,lb_done,zpc,zbase,ncode=64;
static int cfind(const char*n,int l){for(int i=0;i<ncp;i++)if((int)strlen(cp[i].name)==l&&!strncasecmp(cp[i].name,n,l))return i;return -1;}
static int skfind(const char*n,int l){for(int i=0;i<nsk;i++)if((int)strlen(sk[i].name)==l&&!strncasecmp(sk[i].name,n,l))return i;return -1;}
static int knfind(const char*n,int l){for(int i=0;i<nkn;i++)if((int)strlen(kn[i].name)==l&&!strncasecmp(kn[i].name,n,l))return i;return -1;}
static int isid(int c){return isalnum(c)||c=='_';}
#define WD(o,a,b,n) ((uint32_t)(o)|(uint32_t)(a)<<5|(uint32_t)(b)<<9|(uint32_t)(n)<<17)
static const char *P;static int cerr_;static struct{char n[16];int s;}cv[48];static int ncv,cbase;
#define DZ 0
#define DN 1
static void em(int o,int a,int b){if(zpc>=PCS-8){cerr_=1;return;}add_fig(zpc,0,0,WD(o,a,b,zpc+1));zpc++;}
static void emj(int o,int a,int b,int t){if(zpc>=PCS-8){cerr_=1;return;}add_fig(zpc,0,0,WD(o,a,b,t));zpc++;}
static int jf(void){int p=zpc;em(NOP,0,0);return p;}
static void jset(int p,int bit,int val,int t){add_fig(p,1ULL<<bit,(uint64_t)val<<bit,WD(NOP,0,0,t));}
static int resv(void){return zpc++;}
static void jdo(int p,int t){add_fig(p,0,0,WD(NOP,0,0,t));}
static void ws_(void){while(*P==' ')P++;}
static int slot(const char*n,int l){for(int i=0;i<ncv;i++)if((int)strlen(cv[i].n)==l&&!strncmp(cv[i].n,n,l))return cv[i].s;if(ncv>=48||l>15||cbase+ncv>=64){cerr_=1;return 14;}snprintf(cv[ncv].n,16,"%.*s",l,n);cv[ncv].s=cbase+ncv;return cv[ncv++].s;}
static int hasvar(const char*n,int l){for(int i=0;i<ncv;i++)if((int)strlen(cv[i].n)==l&&!strncmp(cv[i].n,n,l))return 1;return 0;}
static void cnum(int64_t v){if(v<0){cnum(-v);em(NEG,3,0);return;}if(v<256){em(LDI,3,v);return;}cnum(v>>8);for(int i=0;i<8;i++)em(SHL,3,0);em(LDI,7,v&255);em(ADD,3,7);}
static void cor(void);
static void callk(int k,int n){for(int i=n-1;i>=0;i--)em(POP,i,0);Known*K=&kn[k];
 if(K->entry)emj(CALL,0,0,K->entry);else{for(int i=n;i<3;i++)em(LDI,i,0);em(LDI,4,K->code);em(SETC,4,0);em(PUSH,11,0);em(LDI,11,1);emj(CALL,0,0,lb_disp);em(POP,11,0);}}
static int args(void){int n=0;ws_();if(*P==')'){P++;return 0;}for(;;){cor();em(PUSH,3,0);n++;ws_();if(*P==','){P++;continue;}if(*P==')'){P++;return n;}cerr_=1;return n;}}
static void idn(char*o,int cap){ws_();int k=0;while(isid((unsigned char)*P)&&k<cap-1)o[k++]=*P++;o[k]=0;ws_();if(*P!=',')cerr_=1;else P++;}
// тело цикла: отдельная подпрограмма, цикл получает её адрес
static int lambda(const char*v1,const char*v2,const char*end){int g=resv();int e=zpc;em(LDI,8,slot(v1,strlen(v1)));em(ST,8,0);if(v2){em(LDI,8,slot(v2,strlen(v2)));em(ST,8,1);}cor();em(RET,0,0);jdo(g,zpc);ws_();if(*P!=*end)cerr_=1;else P++;return e;}
static void comma(void){ws_();if(*P++!=',')cerr_=1;}
static void loop3(const char*nm){char v[16];idn(v,16);cor();em(PUSH,3,0);comma();cor();em(PUSH,3,0);comma();int e=lambda(v,0,")");cnum(e);em(MOV,0,3);em(POP,2,0);em(POP,1,0);int k=knfind(nm,strlen(nm));if(k<0){cerr_=1;return;}emj(CALL,0,0,kn[k].entry);}
static void atom_(void){ws_();if(*P=='('){P++;cor();ws_();if(*P++!=')')cerr_=1;return;}
 if(isdigit((unsigned char)*P)){int64_t v=0;while(isdigit((unsigned char)*P))v=v*10+*P++-'0';cnum(v);return;}
 if(!isalpha((unsigned char)*P)){cerr_=1;return;}const char*s=P;while(isid((unsigned char)*P))P++;int l=P-s;const char*sv=P;ws_();
 if(*P=='('){P++;char u[32];snprintf(u,32,"%.*s",l,s);for(char*q=u;*q;q++)*q=toupper(*q);
  if(!strcmp(u,"ALL")||!strcmp(u,"ANY")||!strcmp(u,"SUM")||!strcmp(u,"COUNT")||!strcmp(u,"PROD")||!strcmp(u,"FIRST")){loop3(u);return;}
  if(!strcmp(u,"IF")){cor();comma();em(MOV,3,3);int f=jf();cor();int e=resv();comma();jset(f,DZ,1,zpc);cor();jdo(e,zpc);ws_();if(*P++!=')')cerr_=1;return;}
  if(!strcmp(u,"FOLD")){char a[16],b[16];idn(a,16);cor();em(PUSH,3,0);comma();idn(b,16);cor();em(PUSH,3,0);comma();cor();em(PUSH,3,0);comma();int e=lambda(a,b,")");cnum(e);em(MOV,0,3);em(POP,2,0);em(POP,1,0);em(POP,3,0);int k=knfind("FOLD",4);if(k<0){cerr_=1;return;}emj(CALL,0,0,kn[k].entry);return;}
  if(!strcmp(u,"ITER")){char x[16];idn(x,16);cor();em(PUSH,3,0);comma();int e1=lambda(x,0,",");int e2=lambda(x,0,")");cnum(e1);em(MOV,0,3);em(PUSH,0,0);cnum(e2);em(MOV,1,3);em(POP,0,0);em(POP,2,0);int k=knfind("ITER",4);if(k<0){cerr_=1;return;}emj(CALL,0,0,kn[k].entry);return;}
  int n=args();int c=cfind(u,strlen(u));if(c>=0){if(n!=cp[c].ar){cerr_=1;return;}for(int i=n-1;i>=0;i--)em(POP,i,0);emj(CALL,0,0,cp[c].entry);return;}int k=knfind(u,strlen(u));if(k<0){cerr_=1;return;}callk(k,n);return;}
 P=sv;if(!hasvar(s,l)){cerr_=1;return;}em(LDI,8,slot(s,l));em(LD,3,8);}
static void cunary(void);
static void cpow_(void){atom_();ws_();if(*P=='^'){P++;em(PUSH,3,0);cunary();em(MOV,1,3);em(POP,0,0);emj(CALL,0,0,lb_pow);}}
static void cunary(void){ws_();if(*P=='-'){P++;cunary();em(NEG,3,0);return;}cpow_();}
static void cmul(void){cunary();for(;;){ws_();char o=*P;if(o!='*'&&o!='/'&&o!='%')return;P++;em(PUSH,3,0);cunary();em(MOV,1,3);em(POP,0,0);emj(CALL,0,0,o=='*'?lb_mul:lb_div);if(o=='%')em(MOV,3,4);}}
static void cadd(void){cmul();for(;;){ws_();char o=*P;if(o!='+'&&o!='-')return;P++;em(PUSH,3,0);cmul();em(MOV,1,3);em(POP,0,0);em(MOV,3,0);em(o=='+'?ADD:SUB,3,1);}}
static void ccmp(void){cadd();ws_();int k=0;if(!strncmp(P,"<=",2))k=1;else if(!strncmp(P,">=",2))k=2;else if(!strncmp(P,"==",2))k=3;else if(!strncmp(P,"!=",2))k=4;else if(*P=='<')k=5;else if(*P=='>')k=6;if(!k)return;P+=k<5?2:1;em(PUSH,3,0);cadd();em(MOV,1,3);em(POP,0,0);
 if(k==1||k==6)em(CMP,1,0);else em(CMP,0,1);em(LDI,3,1);int f=jf();em(LDI,3,0);if(k==1||k==2)jset(f,DN,0,zpc);else if(k==3)jset(f,DZ,1,zpc);else if(k==4)jset(f,DZ,0,zpc);else jset(f,DN,1,zpc);}
static int kw(const char*w){ws_();int l=strlen(w);if(!strncasecmp(P,w,l)&&!isid((unsigned char)P[l])){P+=l;return 1;}return 0;}
static void cnot(void){if(kw("not")){cnot();em(MOV,3,3);em(LDI,3,1);int f=jf();em(LDI,3,0);jset(f,DZ,1,zpc);return;}ccmp();}
static void cand_(void){cnot();while(kw("and")){em(MOV,3,3);int f=jf();cnot();jset(f,DZ,1,zpc);}}
static void cor(void){cand_();while(kw("or")){em(MOV,3,3);int f=jf();cand_();jset(f,DZ,0,zpc);}}
static int heights(const char*t){int h=0;while(*t){if(isalpha((unsigned char)*t)){const char*e=t;while(isid((unsigned char)*e))e++;int c=cfind(t,e-t),k=knfind(t,e-t);if(c>=0&&cp[c].h>h)h=cp[c].h;if(k>=0&&kn[k].h>h)h=kn[k].h;t=e;}else t++;}return h;}
static int comp_add(const char*name,const char*pars,const char*text){Comp C;memset(&C,0,sizeof C);if(!name[0]||strlen(name)>30||ncp>=255||ncode>=255||!lb_disp)return 0;for(const char*c=name;*c;c++)if(!isid((unsigned char)*c))return 0;if(cfind(name,strlen(name))>=0||skfind(name,strlen(name))>=0||knfind(name,strlen(name))>=0)return 0;
 snprintf(C.name,32,"%s",name);for(char*q=C.name;*q;q++)*q=toupper(*q);{char t[64];snprintf(t,64,"%s",pars);char*sv;for(char*a=strtok_r(t,", ",&sv);a;a=strtok_r(0,", ",&sv)){if(C.ar>=3)return 0;snprintf(C.par[C.ar++],16,"%s",a);}}if(!C.ar)return 0;if(!strcmp(C.par[0],"list"))C.islist=1;if(strlen(text)>=1023)return 0;while(*text==' ')text++;strcpy(C.body,text);
 int z0=zpc;cerr_=0;ncv=0;cbase=14+heights(text);C.entry=zpc;for(int i=0;i<C.ar;i++){em(LDI,8,slot(C.par[i],strlen(C.par[i])));em(ST,8,i);}
 static char src[1024];strcpy(src,text);char*sv=0;int last=0;for(char*st=strtok_r(src,";",&sv);st;st=strtok_r(0,";",&sv)){while(*st==' ')st++;char*eq=st;int isl=0;while(isid((unsigned char)*eq))eq++;char*q=eq;while(*q==' ')q++;if(eq>st&&*q=='='&&q[1]!='='){isl=1;}
  if(isl){P=q+1;cor();ws_();if(*P)cerr_=1;em(LDI,8,slot(st,eq-st));em(ST,8,3);}else{P=st;cor();ws_();if(*P)cerr_=1;last=1;}}
 if(!last||cerr_||zpc>=PCS-16){zpc=z0;return 0;}em(RET,0,0);C.h=cbase-14+ncv;C.code=ncode++;int zop=zpc;emj(CALL,0,0,C.entry);emj(NOP,0,0,lb_done);add_fig(lb_disp,0xFFULL<<2,(uint64_t)C.code<<2,WD(NOP,0,0,zop));cp[ncp++]=C;strcpy(sk[nsk].name,C.name);sk[nsk].ar=C.ar;nsk++;return 1;}
// имя составного навыка заменяется кодом, дальше строку читает сеть
static int expand(const char*in,char*o,int cap,int depth){int n=0;while(*in){if(n>=cap-40)return -1;if(isalpha((unsigned char)*in)){const char*e=in;while(isid((unsigned char)*e))e++;int c=cfind(in,e-in);if(c>=0&&*e=='(')n+=sprintf(o+n,"#%d",cp[c].code);else{memcpy(o+n,in,e-in);n+=e-in;}in=e;continue;}o[n++]=*in++;}o[n]=0;return n;}
static char lastplan[200];static int lastnv;
static void seed_skills(void){static const char*s[]={"ABS 1","MIN 2","MAX 2","POW 2","GCD 2","LCM 2","FACT 1","FIB 1","ISQRT 1","PRIME 1","MODPOW 3","NCR 2","NPRIME 1","PHI 1","DIGSUM 1","COLLATZ 1","MODINV 2",0};
 for(int i=0;s[i];i++){sscanf(s[i],"%31s %d",sk[nsk].name,&sk[nsk].ar);nsk++;}}
static uint64_t weights_hash(void){uint64_t h=1469598103934665603ULL;
#define HB(p,n) do{const unsigned char*q_=(const void*)(p);for(size_t i_=0;i_<(size_t)(n);i_++){h^=q_[i_];h*=1099511628211ULL;}}while(0)
 HB(b0,WB*4);HB(O0,(size_t)WB*D*4);for(int i=0;i<NL;i++){Layer*l=&L[i];HB(l->W,(size_t)l->n*l->d*4);HB(l->b,l->n*4);HB(l->P,(size_t)K*l->d*4);HB(l->Q,(size_t)l->n*K*4);HB(l->O,(size_t)WB*l->n*4);}
 for(int q=0;q<PCS;q++)if(memf[q])HB(mem[q],(size_t)memf[q]*sizeof(Fig));return h;}
static void save_mem(const char*p){FILE*f=fopen(p,"w");if(!f)return; fprintf(f,"Z %d\nL %d %d %d %d %d\n",zbase,lb_disp,lb_mul,lb_div,lb_pow,lb_done);for(int i=0;i<nkn;i++)fprintf(f,"K %s %d %d %d\n",kn[i].name,kn[i].code,kn[i].h,kn[i].entry);for(int i=0;i<nsk;i++)if(cfind(sk[i].name,strlen(sk[i].name))<0)fprintf(f,"S %s %d\n",sk[i].name,sk[i].ar);
 for(int q=0;q<PCS;q++)for(int i=0;i<memf[q];i++)fprintf(f,"F %d %" PRIx64 " %" PRIx64 " %x\n",q,mem[q][i].mask,mem[q][i].val,mem[q][i].w);
 for(int i=0;i<ncp;i++){fprintf(f,"D %s %d",cp[i].name,cp[i].ar);for(int k=0;k<cp[i].ar;k++)fprintf(f," %s",cp[i].par[k]);fprintf(f," | %s\n",cp[i].body);}
fclose(f);}
static void load_mem(const char*p){FILE*f=fopen(p,"r");if(!f){perror(p);exit(1);}static char l[2048];int frz=0;while(fgets(l,sizeof l,f)){int q,a;uint64_t m,v;unsigned w;char n[32];if(l[0]=='D'){if(!frz){frz=1;for(int i=0;i<PCS;i++)memf[i]=memn[i];zpc=zbase;}char *bar=strchr(l,'|');if(!bar)continue;*bar=0;char nm[32],pr[64]="";int ar;char a1[16]="",a2[16]="",a3[16]="";sscanf(l,"D %31s %d %15s %15s %15s",nm,&ar,a1,a2,a3);snprintf(pr,64,"%s%s%s%s%s",a1,ar>1?",":"",ar>1?a2:"",ar>2?",":"",ar>2?a3:"");char*b_=bar+2;b_[strcspn(b_,"\n")]=0;comp_add(nm,pr,b_);continue;}
  if(l[0]=='Z'){sscanf(l,"Z %d",&zbase);continue;}if(l[0]=='L'){sscanf(l,"L %d %d %d %d %d",&lb_disp,&lb_mul,&lb_div,&lb_pow,&lb_done);continue;}if(l[0]=='K'){Known*k_=&kn[nkn++];sscanf(l,"K %31s %d %d %d",k_->name,&k_->code,&k_->h,&k_->entry);continue;}
  if(sscanf(l,"S %31s %d",n,&a)==2){strcpy(sk[nsk].name,n);sk[nsk].ar=a;nsk++;}else if(sscanf(l,"F %d %" SCNx64 " %" SCNx64 " %x",&q,&m,&v,&w)==4)add_fig(q,m,v,w);}fclose(f);if(!frz){for(int i=0;i<PCS;i++)memf[i]=memn[i];zpc=zbase;}}
static uint64_t run_lim=3000000;
// Прогон строки на машине под управлением сети, состояние порта не трогается
static int run_text(const char*t,int64_t*res){uint64_t sR[NREG];memcpy(sR,R,sizeof R);int sz=Z,sn=Nf,sc=C,sp_=pc,ssp=sp,scs=csp;static char b[33000];{int n_=expand(t,b,32760,0);if(n_<0)return 0;b[n_]=10;b[n_+1]=0;}
 sub_in=b;sub_len=0;in_sub=1;sp=csp=Z=Nf=C=pc=0;memset(R,0,sizeof R);uint64_t c0=cycles;machine(c0+run_lim);int fin=!*sub_in&&cycles<c0+run_lim&&!err_hw;in_sub=0;err_hw=0;
 memcpy(R,sR,sizeof R);Z=sz;Nf=sn;C=sc;pc=sp_;sp=ssp;csp=scs;sub_out[sub_len]=0;if(!fin||!sub_len||sub_out[0]=='E')return 0;*res=strtoll(sub_out,0,10);return 1;}
static int noexp;
#define MAXE 8
#define MAXA 3000
typedef struct{char s[120];int64_t v[MAXE];}Atom;static Atom *at;static int nat;static char exp_[64][120];static int nexp;
static int ne,nv;static int64_t ein[MAXE][2],eout[MAXE],qin[2];static long tries;
static void subst(const char*t0,const int64_t*in,char*o){const char*t=t0;
#define L(p) ((p)>t0&&isalnum((unsigned char)(p)[-1]))
 for(;*t;t++){if(*t=='a'&&!isalnum((unsigned char)t[1])&&!L(t))o+=sprintf(o,"(%" PRId64 ")",in[0]);else if(*t=='b'&&!isalnum((unsigned char)t[1])&&!L(t))o+=sprintf(o,"(%" PRId64 ")",in[1]);else *o++=*t;}*o=0;}
static uint64_t solve_c0;
static int eval_t(const char*t,const int64_t*in,int64_t*r){if(cycles-solve_c0>40000000)return 0;char b[400];b[0]=' ';subst(t,in,b+1);tries++;return run_text(b+1,r);}
static int check(const char*t,int64_t*ans){for(int i=0;i<ne;i++){int64_t r;if(!eval_t(t,ein[i],&r)||r!=eout[i])return 0;}return eval_t(t,qin,ans);}
static void add_atom(const char*t){if(nat>=MAXA)return;Atom*A=&at[nat];for(int i=0;i<ne;i++)if(!eval_t(t,ein[i],&A->v[i]))return;
 for(int i=0;i<nat;i++)if(!memcmp(at[i].v,A->v,sizeof(int64_t)*ne))return;snprintf(A->s,120,"%s",t);nat++;}
static void report(const char*t,int64_t a){snprintf(lastplan,200,"%s",t);lastnv=nv;char b[300];snprintf(b,300,"%" PRId64 " [план %s, проб %ld]\n",a,t,tries);pout(b);if(!noexp&&nexp<64){for(int i=0;i<nexp;i++)if(!strcmp(exp_[i],t))return;strcpy(exp_[nexp++],t);}}
#include "plan.h"
static void solve(void){tries=0;int64_t ans;solve_c0=cycles;
 if(!noexp)for(int i=nexp-1;i>=0;i--)if(check(exp_[i],&ans)){report(exp_[i],ans);return;}
 if(have_plan&&net_plan())return;          // сначала опыт
 if(!at)at=malloc(sizeof(Atom)*MAXA);nat=0;static const char*base[]={"a","b","a-1","a+1","a*a","a+b","a*b","a-b","b-a"};
 for(int i=0;i<9;i++){if(nv<2&&strchr(base[i],'b'))continue;add_atom(base[i]);}int nbase=nat;char t[120];
 #define TRY(tt) do{int n0=nat;add_atom(tt);if(nat>n0){int ok=1;for(int e=0;e<ne;e++)ok&=at[nat-1].v[e]==eout[e];if(ok){uint64_t sl=run_lim;run_lim=3000000;int g=eval_t(at[nat-1].s,qin,&ans);run_lim=sl;if(g){report(at[nat-1].s,ans);run_lim=3000000;return;}}}}while(0)
 for(int i=0;i<nat;i++){int ok=1;for(int e=0;e<ne;e++)ok&=at[i].v[e]==eout[e];if(ok&&eval_t(at[i].s,qin,&ans)){report(at[i].s,ans);return;}}
 for(int pass=0;pass<2;pass++){run_lim=pass?20000:200000;int lim_b=pass?nbase:(nv>1?2:1);          // сначала навык на самих данных, потом на производных
  for(int s=0;s<nsk;s++){int ar=sk[s].ar;for(int i=0;i<lim_b;i++){if(ar==1){snprintf(t,120,"%s(%s)",sk[s].name,at[i].s);TRY(t);}else if(ar==2)for(int j=0;j<lim_b;j++){snprintf(t,120,"%s(%s,%s)",sk[s].name,at[i].s,at[j].s);TRY(t);}}}}
 run_lim=3000000;
 static const char ops[]="+-*";                                                      // два навыка и арифметика
 for(int i=0;i<nat;i++)for(int j=0;j<nat;j++)for(int o=0;o<3;o++){int ok=1;for(int e=0;e<ne&&ok;e++){int64_t x=at[i].v[e],y=at[j].v[e],r=o==0?x+y:o==1?x-y:x*y;ok=r==eout[e];}
   if(ok){snprintf(t,120,"(%s)%c(%s)",at[i].s,ops[o],at[j].s);if(check(t,&ans)){report(t,ans);return;}}}
 for(int i=0;i<nat;i++)for(int c=1;c<=12;c++)for(int o=0;o<3;o++){int ok=1;for(int e=0;e<ne&&ok;e++){int64_t x=at[i].v[e],r=o==0?x+c:o==1?x-c:x*c;ok=r==eout[e];}
   if(ok){snprintf(t,120,"(%s)%c%d",at[i].s,ops[o],c);if(check(t,&ans)){report(t,ans);return;}}}
 int cap=nat<300?nat:300;run_lim=20000;for(int s=0;s<nsk;s++)if(sk[s].ar==1)for(int i=0;i<cap;i++){int64_t r;char b[150];snprintf(b,150,"%s(%s)",sk[s].name,at[i].s);if(strlen(b)>110)continue;if(!eval_t(b,ein[0],&r)||r!=eout[0])continue;if(check(b,&ans)){run_lim=3000000;report(b,ans);return;}}
 run_lim=3000000;pout("НЕ ЗНАЮ\n");}
// строки порта: DEF, SAVE, раскрытие формул; вернёт длину текста для машины или -1, если строка обработана здесь
static int portfilter(char*l,char*out){char *p=l;while(*p==' ')p++;
 if(!strncasecmp(p,"DEF ",4)){char *o=strchr(p,'('),*c=o?strchr(o,')'):0,*e=c?strchr(c,'='):0;int ok=0;if(e){*o=0;*c=0;char*nm=p+4;while(*nm==' ')nm++;char*z=nm+strlen(nm);while(z>nm&&z[-1]==' ')*--z=0;ok=comp_add(nm,o+1,e+1);}pout(ok?"OK\n":"ERR\n");return -1;}
 if(!strncasecmp(p,"SAVE ",5)){char*nm=p+5;while(*nm==' ')nm++;int ok=0;if(lastplan[0]&&isalpha((unsigned char)nm[0])){char pars[8];strcpy(pars,lastnv>1?"a,b":"a");ok=comp_add(nm,pars,lastplan);}pout(ok?"OK\n":"ERR\n");return -1;}
 if(isalpha((unsigned char)*p)){const char*e=p;while(isid((unsigned char)*e))e++;int c=cfind(p,e-p);if(c>=0&&*e!='('){if(cp[c].islist)return sprintf(out,"LISTQ%s\n#%d(0)\n",e,cp[c].code);return sprintf(out,"#%d%s\n",cp[c].code,e);}}
 int n=expand(l,out,1<<20,0);if(n<0){out[0]='!';n=1;}out[n++]=10;return n;}
static void portline(char*l){if(l[0]=='@'){int q,a;uint64_t m,v;unsigned w;char n[200];
  if(sscanf(l,"@F %d %" SCNx64 " %" SCNx64 " %x",&q,&m,&v,&w)==4){add_fig(q,m,v,w);return;}
  if(sscanf(l,"@S %31s %d",n,&a)==2){strcpy(sk[nsk].name,n);sk[nsk].ar=a;nsk++;return;}
  if(sscanf(l,"@SAVE %199s",n)==1){save_mem(n);pout("@OK\n");return;}
  {int a2,a3,a4,a5;if(sscanf(l,"@K %31s %d %d %d",n,&a2,&a3,&a4)==4){Known*k_=&kn[nkn++];strcpy(k_->name,n);k_->code=a2;k_->h=a3;k_->entry=a4;return;}
   if(sscanf(l,"@L %d %d %d %d %d %d",&a2,&a3,&a4,&a5,&q,&a)==6){lb_disp=a2;lb_mul=a3;lb_div=a4;lb_pow=a5;lb_done=q;zpc=zbase=a;return;}}
  if(!strncmp(l,"@FREEZE",7)){for(int i=0;i<PCS;i++)memf[i]=memn[i];char b[64];snprintf(b,64,"@OK %lx\n",(long)weights_hash());pout(b);return;}
  if(!strncmp(l,"@HASH",5)){char b[96];snprintf(b,96,"@OK %lx refused=%ld\n",(long)weights_hash(),refused);pout(b);return;}
  if(!strncmp(l,"@END",4)){char b[64];snprintf(b,64,"@OK %ld\n",nfig);pout(b);return;}return;}
 ne=0;nv=1;char *p=l+1;
 if(!strncmp(l,"?SEQ",4)){p=l+4;int64_t v;int n,i=1;while(sscanf(p,"%" SCNd64 "%n",&v,&n)==1&&ne<MAXE){ein[ne][0]=i++;ein[ne][1]=0;eout[ne++]=v;p+=n;}qin[0]=i;qin[1]=0;solve();return;}
 char *c=strtok(p,";");int64_t x[8];char *last=0;for(;c;c=strtok(0,";"))last=c,({char*e=strchr(c,'=');if(e&&ne<MAXE){*e=0;char*t=c;int k=0,n;while(sscanf(t,"%" SCNd64 "%n",&x[k],&n)==1&&k<2){k++;t+=n;}nv=k;ein[ne][0]=x[0];ein[ne][1]=k>1?x[1]:0;eout[ne++]=strtoll(e+1,0,10);last=0;}});
 if(!last||!ne){pout("НЕ ЗНАЮ\n");return;}{int k=0,n;char*t=last;while(sscanf(t,"%" SCNd64 "%n",&x[k],&n)==1&&k<2){k++;t+=n;}qin[0]=k?x[0]:0;qin[1]=k>1?x[1]:0;}solve();}
