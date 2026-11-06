// Верхний уровень: сеть выбирает навык по примерам и кладёт упорядоченные планы в память. Проверяют их навыки TRYP и EVALP.
static int PD,PN,PK,PS,have;static char pnames[64][16];static int pid[64];static float *pW,*pb,*pP,*pQ,*pO,*pcb;
static const int HEADS[6]={4,9,9,3,12,9};static const char*ARGS[9]={"a","b","a-1","a+1","a*a","a+b","a*b","a-b","b-a"};
static void load_plan(const char*p){FILE*f=fopen(p,"rb");if(!f)return;fseek(f,0,SEEK_END);long l=ftell(f);rewind(f);char*b=malloc(l),*q=b+20;if(fread(b,1,l,f)!=(size_t)l)exit(1);fclose(f);uint32_t*h=(void*)(b+4);PD=h[0];PN=h[1];PK=h[2];PS=h[3];memcpy(pnames,q,16*PS);q+=16*PS;for(int i=0;i<PS;i++){pid[i]=-1;for(int j=0;j<NM;j++)if(!strcmp(M[j].name,pnames[i]))pid[i]=j;}
 int out=PS;for(int i=0;i<6;i++)out+=HEADS[i];pW=rd(&q,(size_t)PN*PD);pb=rd(&q,PN);pP=rd(&q,(size_t)PK*PD);pQ=rd(&q,(size_t)PN*PK);pO=rd(&q,(size_t)out*PN);pcb=rd(&q,out);have=1;}
static int isq(int64_t n){if(n<0)return 0;int64_t s=(int64_t)sqrtl((long double)n);while(s*s>n)s--;while((s+1)*(s+1)<=n)s++;return s*s==n;}
static int isp_(int64_t n){if(n<2)return 0;for(int64_t i=2;i*i<=n;i++)if(n%i==0)return 0;return 1;}
static void feats(int ne,int nv,float*F){int n=ne<4?ne:4;int64_t E[4][3];for(int i=0;i<n;i++){E[i][0]=ram[51000+3*i];E[i][1]=ram[51001+3*i];E[i][2]=ram[51002+3*i];}
 for(int i=1;i<n;i++)for(int j=i;j>0;j--){if(E[j][0]<E[j-1][0]||(E[j][0]==E[j-1][0]&&E[j][1]<E[j-1][1])){int64_t t[3];memcpy(t,E[j],24);memcpy(E[j],E[j-1],24);memcpy(E[j-1],t,24);}}
 for(int i=n;i<4;i++)memcpy(E[i],E[n-1],24);int k=0;
 for(int i=0;i<4;i++){int64_t a=E[i][0],b=E[i][1],r=E[i][2],ar=r<0?-r:r;double la=log1p(llabs(a)),lb=log1p(llabs(b)),lr=log1p((double)ar);
  F[k++]=lr/10;F[k++]=(lr-la)/5;F[k++]=(lr-lb)/5;F[k++]=lr/(la+1)/3;F[k++]=r==a;F[k++]=r==b;F[k++]=r==0;F[k++]=r==1;F[k++]=ar%2;F[k++]=r%3==0;F[k++]=r<a;F[k++]=r<b;F[k++]=(__int128)r>(__int128)a*b;
  F[k++]=a&&r%a==0;F[k++]=b&&r%b==0;F[k++]=r&&a%r==0;F[k++]=r&&b%r==0;F[k++]=isq(ar);F[k++]=ar<10;F[k++]=r<0;F[k++]=ar<(1LL<<30)&&isp_(ar);}
 double lr[4],la[4];for(int i=0;i<4;i++){lr[i]=log1p((double)llabs(E[i][2]));la[i]=log1p(llabs(E[i][0]));}int mono=lr[0]<=lr[1]&&lr[1]<=lr[2]&&lr[2]<=lr[3];int u=1;for(int i=1;i<4;i++){int d=1;for(int j=0;j<i;j++)d&=E[j][2]!=E[i][2];u+=d;}double mx=lr[0];for(int i=1;i<4;i++)if(lr[i]>mx)mx=lr[i];
 F[k++]=nv==2;F[k++]=mono;F[k++]=(lr[3]-lr[0])/(la[3]-la[0]+.1)/3;F[k++]=(lr[3]-lr[0])/((double)(E[3][0]-E[0][0])+1);F[k++]=u/4.0;F[k++]=mx/10;}
typedef struct{double s;int form,f,g,x,y,op,c,gx;}Pl;static Pl *LP;
static int cmpP(const void*a,const void*b){double d=((Pl*)b)->s-((Pl*)a)->s;return d<0?-1:d>0;}
static int ord[64],TS_;static double ls[64],lp[6][16];static int NV_;
static int plan(int ne){if(!have||ne<1)return 0;int nv=ram[50999];NV_=nv;static float x[1024],h[8192],y[256];float z[64];feats(ne,nv,x);
 for(int k=0;k<PK;k++){float s=0;const float*p=pP+(size_t)k*PD;for(int j=0;j<PD;j++)s+=p[j]*x[j];z[k]=s*s;}
 for(int i=0;i<PN;i++){float s=pb[i];const float*w=pW+(size_t)i*PD;for(int j=0;j<PD;j++)s+=w[j]*x[j];const float*q=pQ+(size_t)i*PK;for(int k=0;k<PK;k++)s+=q[k]*z[k];h[i]=s>0?s:0;}
 int out=PS;for(int i=0;i<6;i++)out+=HEADS[i];for(int b=0;b<out;b++){float s=pcb[b];const float*o=pO+(size_t)b*PN;for(int j=0;j<PN;j++)s+=o[j]*h[j];y[b]=s;}
 int o=PS;for(int i=0;i<6;i++){double m=-1e30,t=0;for(int j=0;j<HEADS[i];j++)if(y[o+j]>m)m=y[o+j];for(int j=0;j<HEADS[i];j++)t+=exp(y[o+j]-m);for(int j=0;j<HEADS[i];j++)lp[i][j]=y[o+j]-m-log(t);o+=HEADS[i];}
 for(int i=0;i<PS;i++){ord[i]=i;ls[i]=-log1p(exp(-y[i]));}for(int i=1;i<PS;i++)for(int j=i;j>0&&ls[ord[j]]>ls[ord[j-1]];j--){int t=ord[j];ord[j]=ord[j-1];ord[j-1]=t;}
 int TS=PS<8?PS:8;TS_=TS;if(!LP)LP=malloc(sizeof(Pl)*3000000);long n=0;
 #define OKA(i) (nv>1||!strchr(ARGS[i],'b'))
 for(int fi=0;fi<TS;fi++){int f=ord[fi];if(pid[f]<0)continue;int ar=M[pid[f]].ar;if(ar>2)continue;for(int x_=0;x_<9;x_++){if(!OKA(x_))continue;for(int y_=0;y_<(ar==2?9:1);y_++){if(ar==2&&!OKA(y_))continue;double b=ls[f]+lp[1][x_]+(ar==2?lp[2][y_]:0);
  LP[n++]=(Pl){b+lp[0][0],0,f,0,x_,y_,0,0,0};for(int op=0;op<3;op++)for(int c=1;c<=12;c++)LP[n++]=(Pl){b+lp[0][2]+lp[3][op]+lp[4][c-1],2,f,0,x_,y_,op,c,0};
  for(int gi=0;gi<TS;gi++){int g=ord[gi];if(pid[g]<0)continue;int ag=M[pid[g]].ar;if(ag==1)LP[n++]=(Pl){b+lp[0][3]+ls[g],3,f,g,x_,y_,0,0,0};if(gi>=fi&&ag<=2&&n<2900000)for(int gx=0;gx<9;gx++){if(!OKA(gx))continue;for(int op=0;op<3;op++)LP[n++]=(Pl){b+lp[0][1]+ls[g]+lp[5][gx]+lp[3][op],1,f,g,x_,y_,op,0,gx};}}}}if(n>2800000)break;}
 qsort(LP,n,sizeof(Pl),cmpP);if(n>600)n=600;for(long i=0;i<n;i++){Pl*p=&LP[i];int64_t*q=&ram[52000+8*i];q[0]=p->form;q[1]=pid[p->f];q[2]=p->form==1||p->form==3?pid[p->g]:0;q[3]=p->x;q[4]=p->y;q[5]=p->op;q[6]=p->c;q[7]=p->gx;}return n;}
// вероятные навыки считаются по одному разу, дальше навыки COMBO и NEST сочетают готовые результаты
static int unary_k(int k){if(k>=TS_)return -1;int f=ord[k];if(pid[f]<0||M[pid[f]].ar!=1)return -1;return pid[f];}
static int atoms(void){int nv=NV_;Pl *A=malloc(sizeof(Pl)*20000);int n=0;
#undef OKA
#define OKA(i) (nv>1||!strchr(ARGS[i],'b'))
 int K_=PS;for(int fi=0;fi<K_;fi++){int f=ord[fi];if(pid[f]<0)continue;int ar=M[pid[f]].ar;if(ar>2)continue;for(int x_=0;x_<9;x_++){if(!OKA(x_))continue;for(int y_=0;y_<(ar==2?9:1);y_++){if(ar==2&&!OKA(y_))continue;A[n++]=(Pl){ls[f]+lp[1][x_]+(ar==2?lp[2][y_]:0)+(x_<2&&(ar==1||y_<2)?30:0),0,f,0,x_,y_,0,0,0};}}}
 for(int i=0;i<PS;i++)if(!strcmp(pnames[i],"ABS")&&pid[i]>=0){A[n++]=(Pl){100,0,i,0,0,0,0,0,0};if(nv>1)A[n++]=(Pl){100,0,i,0,1,0,0,0,0};}
 qsort(A,n,sizeof(Pl),cmpP);if(n>130)n=130;for(int i=0;i<n;i++){LP[625+i]=A[i];Pl*p=&A[i];int64_t*q=&ram[57000+8*i];q[0]=0;q[1]=pid[p->f];q[2]=0;q[3]=p->x;q[4]=p->y;q[5]=0;q[6]=0;q[7]=0;}free(A);return n;}
static void atxt(int i,char*u){Pl*p=&LP[625+i];const char*F=pnames[p->f];if(M[pid[p->f]].ar==1)snprintf(u,60,"%s(%s)",F,ARGS[p->x]);else snprintf(u,60,"%s(%s,%s)",F,ARGS[p->x],ARGS[p->y]);}
static void txcombo(int i,int j,int o){char u[60],v[60],b[200];atxt(i,u);if(j==999){snprintf(b,200," [план (%s)%c%d]",u,"+-*"[o>>4],o&15);txs(b);return;}atxt(j,v);snprintf(b,200," [план (%s)%c(%s)]",u,"+-*"[o],v);txs(b);}
static void txnest(int g,int i){char u[60],b[200];atxt(i,u);snprintf(b,200," [план %s(%s)]",M[g].name,u);txs(b);}
static void txplan(int64_t i){if(i==99999999){txs("НЕ ЗНАЮ\n");return;}Pl*p=&LP[i];char u[60],v[60],o[200];const char*F=pnames[p->f];if(M[pid[p->f]].ar==1)snprintf(u,60,"%s(%s)",F,ARGS[p->x]);else snprintf(u,60,"%s(%s,%s)",F,ARGS[p->x],ARGS[p->y]);
 if(p->form==0)strcpy(o,u);else if(p->form==2)sprintf(o,"(%s)%c%d",u,"+-*"[p->op],p->c);else if(p->form==3)sprintf(o,"%s(%s)",pnames[p->g],u);else{const char*G=pnames[p->g];if(M[pid[p->g]].ar==1)snprintf(v,60,"%s(%s)",G,ARGS[p->gx]);else snprintf(v,60,"%s(%s,%s)",G,ARGS[p->gx],ARGS[p->y]);sprintf(o,"(%s)%c(%s)",u,"+-*"[p->op],v);}
 txs(" [план ");txs(o);txs("]");}
