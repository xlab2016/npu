// Сеть-планировщик: по примерам задачи предсказывает навыки и форму плана. Перебор остаётся запасным путём.
static int PD,PN,PK,PS;static char pnames[64][16];static float *pW,*pb,*pP,*pQ,*pO,*pcb;static int have_plan;
static const int HEADS[6]={4,9,9,3,12,9};static const char*ARGS[9]={"a","b","a-1","a+1","a*a","a+b","a*b","a-b","b-a"};
static void load_plan(const char*p){FILE*f=fopen(p,"rb");if(!f){perror(p);exit(1);}char m[4];uint32_t h[4];if(fread(m,1,4,f)!=4||fread(h,4,4,f)!=4)exit(1);PD=h[0];PN=h[1];PK=h[2];PS=h[3];if(fread(pnames,16,PS,f)!=(size_t)PS)exit(1);
 int out=PS;for(int i=0;i<6;i++)out+=HEADS[i];pW=rd(f,(size_t)PN*PD);pb=rd(f,PN);pP=rd(f,(size_t)PK*PD);pQ=rd(f,(size_t)PN*PK);pO=rd(f,(size_t)out*PN);pcb=rd(f,out);fclose(f);have_plan=1;}
static int isq(int64_t n){if(n<0)return 0;int64_t s=(int64_t)sqrtl((long double)n);while(s*s>n)s--;while((s+1)*(s+1)<=n)s++;return s*s==n;}
static int isp_(int64_t n){if(n<2)return 0;for(int64_t i=2;i*i<=n;i++)if(n%i==0)return 0;return 1;}
static void feats(float*F){int id[4],n=ne<4?ne:4;for(int i=0;i<n;i++)id[i]=i;
 double e[4][3];int m=n;for(int i=0;i<m;i++){e[i][0]=0;}
 int64_t E[4][3];for(int i=0;i<n;i++){E[i][0]=ein[i][0];E[i][1]=ein[i][1];E[i][2]=eout[i];}
 for(int i=1;i<n;i++)for(int j=i;j>0;j--){if(E[j][0]<E[j-1][0]||(E[j][0]==E[j-1][0]&&E[j][1]<E[j-1][1])){int64_t t[3];memcpy(t,E[j],24);memcpy(E[j],E[j-1],24);memcpy(E[j-1],t,24);}}
 for(int i=n;i<4;i++)memcpy(E[i],E[n-1],24);int k=0;
 for(int i=0;i<4;i++){int64_t a=E[i][0],b=E[i][1],r=E[i][2],ar=r<0?-r:r;double la=log1p(llabs(a)),lb=log1p(llabs(b)),lr=log1p((double)ar);
  F[k++]=lr/10;F[k++]=(lr-la)/5;F[k++]=(lr-lb)/5;F[k++]=lr/(la+1)/3;F[k++]=r==a;F[k++]=r==b;F[k++]=r==0;F[k++]=r==1;F[k++]=ar%2;F[k++]=r%3==0;F[k++]=r<a;F[k++]=r<b;F[k++]=(__int128)r>(__int128)a*b;
  F[k++]=a&&r%a==0;F[k++]=b&&r%b==0;F[k++]=r&&a%r==0;F[k++]=r&&b%r==0;F[k++]=isq(ar);F[k++]=ar<10;F[k++]=r<0;F[k++]=ar<(1LL<<30)&&isp_(ar);}
 double lr[4],la[4];for(int i=0;i<4;i++){lr[i]=log1p((double)llabs(E[i][2]));la[i]=log1p(llabs(E[i][0]));}
 int mono=lr[0]<=lr[1]&&lr[1]<=lr[2]&&lr[2]<=lr[3];int u=1;for(int i=1;i<4;i++){int d=1;for(int j=0;j<i;j++)d&=E[j][2]!=E[i][2];u+=d;}double mx=lr[0];for(int i=1;i<4;i++)if(lr[i]>mx)mx=lr[i];
 F[k++]=nv==2;F[k++]=mono;F[k++]=(lr[3]-lr[0])/(la[3]-la[0]+.1)/3;F[k++]=(lr[3]-lr[0])/((double)(E[3][0]-E[0][0])+1);F[k++]=u/4.0;F[k++]=mx/10;}
typedef struct{double s;short form,f,x,y,g,gx,gy,op,c;}Plan;
static int cmpP(const void*a,const void*b){double d=((Plan*)b)->s-((Plan*)a)->s;return d<0?-1:d>0;}
static int skar(const char*n){for(int i=0;i<nsk;i++)if(!strcmp(sk[i].name,n))return sk[i].ar;return 0;}
static void ptext(const Plan*p,char*o){char u[60],v[60];const char*F=pnames[p->f];if(skar(F)==1)snprintf(u,60,"%s(%s)",F,ARGS[p->x]);else snprintf(u,60,"%s(%s,%s)",F,ARGS[p->x],ARGS[p->y]);
 if(p->form==0)strcpy(o,u);else if(p->form==2)sprintf(o,"(%s)%c%d",u,"+-*"[p->op],p->c);else if(p->form==3)sprintf(o,"%s(%s)",pnames[p->g],u);
 else{const char*G=pnames[p->g];if(skar(G)==1)snprintf(v,60,"%s(%s)",G,ARGS[p->gx]);else snprintf(v,60,"%s(%s,%s)",G,ARGS[p->gx],ARGS[p->y]);sprintf(o,"(%s)%c(%s)",u,"+-*"[p->op],v);}}
// вернёт 1, если сеть решила; plans_tried считает, сколько планов она предложила
static long plans_tried;
static int net_plan(void){static float x[2048],h[8192],y[256];float z[64];feats(x);if(PN>8192)return 0;
 for(int k=0;k<PK;k++){float s=0;const float*p=pP+(size_t)k*PD;for(int j=0;j<PD;j++)s+=p[j]*x[j];z[k]=s*s;}
 for(int i=0;i<PN;i++){float s=pb[i];const float*w=pW+(size_t)i*PD;for(int j=0;j<PD;j++)s+=w[j]*x[j];const float*q=pQ+(size_t)i*PK;for(int k=0;k<PK;k++)s+=q[k]*z[k];h[i]=s>0?s:0;}
 int out=PS;for(int i=0;i<6;i++)out+=HEADS[i];for(int b=0;b<out;b++){float s=pcb[b];const float*o=pO+(size_t)b*PN;for(int j=0;j<PN;j++)s+=o[j]*h[j];y[b]=s;}
 double lp[6][16];int o=PS;for(int i=0;i<6;i++){double m=-1e30,t=0;for(int j=0;j<HEADS[i];j++)if(y[o+j]>m)m=y[o+j];for(int j=0;j<HEADS[i];j++)t+=exp(y[o+j]-m);for(int j=0;j<HEADS[i];j++)lp[i][j]=y[o+j]-m-log(t);o+=HEADS[i];}
 int ord[64];double ls[64];for(int i=0;i<PS;i++){ord[i]=i;ls[i]=-log1p(exp(-y[i]));}for(int i=1;i<PS;i++)for(int j=i;j>0&&ls[ord[j]]>ls[ord[j-1]];j--){int t=ord[j];ord[j]=ord[j-1];ord[j-1]=t;}
 {typedef struct{double s;int i;}CS;CS cs[256];int nc=0;for(int c=0;c<ncp;c++){double t_=0;int k_=0;const char*q=cp[c].body;
   while(*q){if(isalpha((unsigned char)*q)){const char*e=q;while(isid((unsigned char)*e))e++;for(int i=0;i<PS;i++)if((int)strlen(pnames[i])==e-q&&!strncasecmp(pnames[i],q,e-q)){t_+=ls[i];k_++;}int c2=cfind(q,e-q);if(c2>=0){k_++;t_+=-3;}q=e;}else q++;}
   if(k_&&(cp[c].ar==nv||cp[c].ar==1)){cs[nc].s=t_/k_;cs[nc++].i=c;}}
  for(int i=1;i<nc;i++)for(int j=i;j>0&&cs[j].s>cs[j-1].s;j--){CS v=cs[j];cs[j]=cs[j-1];cs[j-1]=v;}
  int64_t a_;char t_[80];run_lim=300000;for(int i=0;i<nc&&i<6;i++){Comp*C=&cp[cs[i].i];if(C->ar==1)snprintf(t_,80,"%s(a)",C->name);else snprintf(t_,80,"%s(a,b)",C->name);if(check(t_,&a_)){run_lim=3000000;report(t_,a_);return 1;}}}
 int TS=PS<10?PS:10;static Plan *L;if(!L)L=malloc(sizeof(Plan)*2000000);long n=0;
 #define OKA(i) (nv>1||!strchr(ARGS[i],'b'))
 for(int fi=0;fi<TS;fi++){int f=ord[fi];int ar=skar(pnames[f]);if(!ar||ar>2)continue;for(int x_=0;x_<9;x_++){if(!OKA(x_))continue;for(int y_=0;y_<(ar==2?9:1);y_++){if(ar==2&&!OKA(y_))continue;double b=ls[f]+lp[1][x_]+(ar==2?lp[2][y_]:0);
  L[n++]=(Plan){b+lp[0][0],0,f,x_,y_,0,0,0,0,0};
  for(int op=0;op<3;op++)for(int c=1;c<=12;c++)L[n++]=(Plan){b+lp[0][2]+lp[3][op]+lp[4][c-1],2,f,x_,y_,0,0,0,op,c};
  for(int gi=0;gi<TS;gi++){int g=ord[gi];int ag=skar(pnames[g]);if(ag==1&&n<1900000)L[n++]=(Plan){b+lp[0][3]+ls[g],3,f,x_,y_,g,0,0,0,0};
   if(gi>=fi&&ag>0&&ag<=2&&n<1900000)for(int gx=0;gx<9;gx++){if(!OKA(gx))continue;for(int op=0;op<3;op++)L[n++]=(Plan){b+lp[0][1]+ls[g]+lp[5][gx]+lp[3][op],1,f,x_,y_,g,gx,0,op,0};}}}}
  if(n>1800000)break;}
 qsort(L,n,sizeof(Plan),cmpP);int64_t ans;char t[200];run_lim=200000;long maxp=n<4000?n:4000;uint64_t c0=cycles;
 for(long i=0;i<maxp;i++){if(cycles-c0>4000000)break;
  if(i==60){ // навыки, которые сеть считает вероятными, считаем один раз и сочетаем без новых запусков
   if(!at)at=malloc(sizeof(Atom)*MAXA);nat=0;int ao[9],na=0;for(int j=0;j<9;j++)ao[j]=j;for(int j=1;j<9;j++)for(int q=j;q>0&&lp[1][ao[q]]>lp[1][ao[q-1]];q--){int v=ao[q];ao[q]=ao[q-1];ao[q-1]=v;}
   add_atom("a");if(nv>1)add_atom("b");run_lim=100000;
   for(int fi=0;fi<TS;fi++){int f=ord[fi],ar=skar(pnames[f]);if(!ar||ar>2)continue;for(int u=0;u<9&&u<5;u++){if(!OKA(ao[u]))continue;if(ar==1){snprintf(t,200,"%s(%s)",pnames[f],ARGS[ao[u]]);add_atom(t);}else for(int w=0;w<5;w++){if(!OKA(ao[w]))continue;snprintf(t,200,"%s(%s,%s)",pnames[f],ARGS[ao[u]],ARGS[ao[w]]);add_atom(t);}}}
   {int top=ncp;for(int c_=top-1;c_>=0&&c_>=top-6;c_--){if(cp[c_].ar!=1)continue;char q_[80];snprintf(q_,80,"%s(a)",cp[c_].name);add_atom(q_);for(int gi=0;gi<TS;gi++){int g=ord[gi];if(skar(pnames[g])==1){snprintf(t,200,"%s(%s)",pnames[g],q_);add_atom(t);}}}}   // замороженные формулы служат опорой для следующего шага
   for(int a_=0;a_<nat;a_++)for(int c_=1;c_<=12;c_++)for(int o_=0;o_<3;o_++){int ok=1;for(int e_=0;e_<ne&&ok;e_++){int64_t X=at[a_].v[e_];ok=(o_==0?X+c_:o_==1?X-c_:X*c_)==eout[e_];}
    if(ok){snprintf(t,200,"(%s)%c%d",at[a_].s,"+-*"[o_],c_);if(check(t,&ans)){run_lim=3000000;report(t,ans);return 1;}}}
   for(int a_=0;a_<nat;a_++)for(int b_=0;b_<nat;b_++)for(int o_=0;o_<3;o_++){int ok=1;for(int e_=0;e_<ne&&ok;e_++){int64_t X=at[a_].v[e_],Y=at[b_].v[e_];ok=(o_==0?X+Y:o_==1?X-Y:X*Y)==eout[e_];}
    if(ok){snprintf(t,200,"(%s)%c(%s)",at[a_].s,"+-*"[o_],at[b_].s);if(check(t,&ans)){run_lim=3000000;report(t,ans);return 1;}}}
   run_lim=30000;for(int gi=0;gi<TS;gi++){int g=ord[gi];if(skar(pnames[g])!=1)continue;for(int a_=0;a_<nat;a_++){int64_t r;snprintf(t,200,"%s(%s)",pnames[g],at[a_].s);if(!eval_t(t,ein[0],&r)||r!=eout[0])continue;if(check(t,&ans)){run_lim=3000000;report(t,ans);return 1;}}}
  }
  run_lim=i<60?300000:20000;ptext(&L[i],t);plans_tried=i+1;if(check(t,&ans)){run_lim=3000000;report(t,ans);return 1;}}
 run_lim=3000000;return 0;}
