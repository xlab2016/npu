// Скорость прямого прохода одного слоя для разных геометрических нейронов.
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#define D 64
#define N 256
#define K 16
#define R 2
#define HARM 4
static float x[D],W[N][D],b[N],lam[N],P[K][D],Q[N][K],A[N][R][D],c[N][D],pw[N],V[N][HARM][R],ph[N][HARM],am[N][HARM],h[N];
static double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+1e-9*t.tv_nsec;}
static float rf(){return (float)rand()/RAND_MAX*2-1;}
#define RELU(v) ((v)>0?(v):0)
__attribute__((noinline)) void mlp(){for(int i=0;i<N;i++){float s=b[i];for(int j=0;j<D;j++)s+=W[i][j]*x[j];h[i]=RELU(s);}}
__attribute__((noinline)) void conf(){float q=0;for(int j=0;j<D;j++)q+=x[j]*x[j];
 for(int i=0;i<N;i++){float s=b[i]+lam[i]*q;for(int j=0;j<D;j++)s+=W[i][j]*x[j];h[i]=RELU(s);}}
__attribute__((noinline)) void shared(){float z[K];for(int k=0;k<K;k++){float s=0;for(int j=0;j<D;j++)s+=P[k][j]*x[j];z[k]=s*s;}
 for(int i=0;i<N;i++){float s=b[i];for(int j=0;j<D;j++)s+=W[i][j]*x[j];for(int k=0;k<K;k++)s+=Q[i][k]*z[k];h[i]=RELU(s);}}
__attribute__((noinline)) void lowrank(){for(int i=0;i<N;i++){float s=b[i];for(int j=0;j<D;j++)s+=W[i][j]*x[j];
 for(int r=0;r<R;r++){float t=0;for(int j=0;j<D;j++)t+=A[i][r][j]*x[j];s-=t*t;}h[i]=RELU(s);}}
__attribute__((noinline)) void feron(){for(int i=0;i<N;i++){float z[R],nn=0,dot=0;for(int r=0;r<R;r++){float t=0;for(int j=0;j<D;j++)t+=A[i][r][j]*(x[j]-c[i][j]);z[r]=t;}
 float e=2+fabsf(pw[i]);for(int r=0;r<R;r++)nn+=powf(fabsf(z[r])+1e-4f,e);nn=powf(nn,1/e);
 float rho=0;for(int m=0;m<HARM;m++){float t=ph[i][m];for(int r=0;r<R;r++)t+=V[i][m][r]*z[r]/(nn+1e-4f);rho+=am[i][m]*cosf(t);}
 float rad=nn/expf(rho);for(int j=0;j<D;j++)dot+=W[i][j]*(x[j]-c[i][j]);float lin=1+dot;float f=lam[i]*rad+(1-lam[i])*lin;h[i]=1/(1+expf(-4*(1-f)));}}
static void run(const char*n,void(*f)(void),double base,double*out){double t=now();long c=0;volatile float sink=0;
 while(now()-t<1.0){for(int i=0;i<2000;i++){x[i%D]=-x[i%D];f();sink+=h[i%N];}c+=2000;}
 double us=(now()-t)/c*1e6;printf("%-22s %9.2f мкс  %12.0f проходов/с",n,us,1e6/us);if(base>0)printf("  x%.2f",us/base);puts("");*out=us;}
int main(){for(int j=0;j<D;j++)x[j]=rf();for(int i=0;i<N;i++){b[i]=rf();lam[i]=rf();pw[i]=rf();for(int j=0;j<D;j++){W[i][j]=rf();c[i][j]=rf();}for(int k=0;k<K;k++)Q[i][k]=rf();
 for(int r=0;r<R;r++)for(int j=0;j<D;j++)A[i][r][j]=rf();for(int m=0;m<HARM;m++){ph[i][m]=rf();am[i][m]=rf()*.2;for(int r=0;r<R;r++)V[i][m][r]=rf();}}
 for(int k=0;k<K;k++)for(int j=0;j<D;j++)P[k][j]=rf();
 double b0,t;printf("слой: вход %d, нейронов %d\n",D,N);run("MLP",mlp,0,&b0);run("сфера+плоскость",conf,b0,&t);run("общие оси k=16",shared,b0,&t);run("эллипсоид r=2",lowrank,b0,&t);run("полный ферон",feron,b0,&t);}
