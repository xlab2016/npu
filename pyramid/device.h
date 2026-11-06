// Адаптер устройства: настоящие действия выполняет внешний сценарий. Здесь нет логики обновления.
static char UF[32][48],UO[64][48],UD[64][80];static int UNF,UNO;
#ifdef _WIN32
static const char*devp="powershell -NoProfile -ExecutionPolicy Bypass -File device.ps1";
#else
static const char*devp="./device.sh";
#endif
static void load_update(void){FILE*f=fopen("update.tab","r");if(!f)return;char l[512];while(fgets(l,sizeof l,f)){l[strcspn(l,"\n")]=0;long long a,b,c,d;int e;if(l[0]=='H'){sscanf(l,"H %lld %lld %lld %lld %d",&a,&b,&c,&d,&e);ram[61990]=a;ram[61991]=b;ram[61992]=c;ram[61993]=d;}else if(l[0]=='F')snprintf(UF[UNF++],48,"%s",l+2);else if(l[0]=='O'){char id[48];int n;sscanf(l,"O %47s %lld %lld %lld %lld %n",id,&a,&b,&c,&d,&n);strcpy(UO[UNO],id);snprintf(UD[UNO],80,"%s",l+n);int64_t*q=&ram[62000+5*UNO];q[0]=a;q[1]=b;q[2]=c;q[3]=d;UNO++;}}fclose(f);const char*e=getenv("NPU_DEVICE");if(e)devp=e;}
static int fbit(const char*s){for(int i=0;i<UNF;i++)if(!strcmp(UF[i],s))return i;return -1;}
static int64_t dev_observe(void){char c[300];snprintf(c,300,"%s observe 2>&1",devp);FILE*p=popen(c,"r");int64_t m=0;int bl=0;if(!p){ram[63300]=1;return 0;}char l[512];while(fgets(l,sizeof l,p)){l[strcspn(l,"\r\n")]=0;if(!strncmp(l,"BLOCK ",6)){bl++;txs("БЛОКИРОВКА: ");txs(l+6);txb('\n');}else{int b=fbit(l);if(b>=0)m|=1LL<<b;}}if(pclose(p)!=0&&!bl){bl=1;txs("БЛОКИРОВКА: не удалось прочитать состояние\n");}ram[63300]=bl;return m;}
static int64_t dev_run(int i){char c[300];snprintf(c,300,"%s run %s 2>&1",devp,UO[i]);flushz();txs("> ");txs(UO[i]);txb('\n');FILE*p=popen(c,"r");if(!p)return 99;char l[512],last[512]="";while(fgets(l,sizeof l,p)){l[strcspn(l,"\r\n")]=0;strcpy(last,l);txs("  | ");txs(l);txb('\n');}int st=pclose(p);if(st==0)return 0;int b=fbit(last);if(b>=0)return b+1;return 99;}
static void txop(int k,int i){char b[200];if(k==0)snprintf(b,200,"СБОЙ в %s\n",UO[i]);else snprintf(b,200,"%d. %s — %s\n",k,UO[i],UD[i]);txs(b);}
static void txmsg(int k){static const char*m[]={"Ждёт подтверждения: APPROVE или CANCEL\n","ГОТОВО: цель достигнута\n","ОБНОВЛЕНИЕ ЗАПРЕЩЕНО: сначала устраните блокировки\n","НЕТ БЕЗОПАСНОГО ПЛАНА\n","НЕТ ПЛАНА ДЛЯ ПОДТВЕРЖДЕНИЯ: сначала UPDATE\n","ПЛАН ВОССТАНОВЛЕНИЯ:\n","ОТМЕНЕНО\n"};txs(m[k]);}
static void txfacts(int64_t f){for(int i=0;i<UNF;i++)if(f>>i&1){txs(UF[i]);txb(' ');}txb('\n');}
