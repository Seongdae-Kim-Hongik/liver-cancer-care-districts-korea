# 98_fit_forced_v — 98_fit_forced.R 사본(2026-10-19): MODE 에 std2·std3 추가(std3 = panel_<TAG>_std3 의 E·강제통제 그대로)(offset E_std2 = 02_패널/<TAG>_Estd2.csv, 강제통제 = forced − older_adult_share). 원본은 그대로.
#  사용(01_스크립트/에서): Rscript 98_fit_forced_v.R <TAG> std2   → 04_분석/<TAG>/results_screen/forced_std2_{RR,hyper}.csv (새 이름)
suppressPackageStartupMessages({library(INLA);library(sf);library(spdep);library(jsonlite)})
a<-commandArgs(trailingOnly=TRUE);TAG<-a[1];MODE<-a[2];stopifnot(MODE%in%c("crude","std","std2","std3"))
inla.setOption(num.threads="1:1")
D<-file.path("..","04_분석",TAG);OUT<-file.path(D,"results_screen");dir.create(OUT,showWarnings=FALSE)
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
S<-fromJSON(file.path(D,sprintf("config_%s.json",TAG)),simplifyVector=TRUE)
DD<-read.csv(file.path(D,sprintf("panel_%s.csv",TAG)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
FORCED<-S$forced
if(MODE=="std3"){S<-fromJSON(file.path(D,sprintf("config_%s_std3.json",TAG)),simplifyVector=TRUE);DD<-read.csv(file.path(D,sprintf("panel_%s_std3.csv",TAG)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region);FORCED<-S$forced}   # std3: 패널 E = E_std2, 강제통제 = std3 forced(80+ 포함)
if(MODE%in%c("std","std2")){ES<-read.csv(file.path("..","02_패널",sprintf(if(MODE=="std2")"%s_Estd2.csv" else "%s_Estd.csv",TAG)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);ES$fbd_region<-enc2utf8(ES$fbd_region)
  k<-match(paste(DD$fbd_region,DD$year),paste(ES$fbd_region,ES$year));stopifnot(!anyNA(k));DD$E<-ES[[if(MODE=="std2")"E_std2" else "E_std"]][k];FORCED<-setdiff(FORCED,"older_adult_share")}
DD<-DD[DD$E>0,]
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);stopifnot(all(DD$fbd_region%in%G$region))
g<-inla.read.graph(file.path(D,"results",sprintf("nb_%s.graph",TAG)));stopifnot(g$n==nrow(G))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
form<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",FORCED),collapse="+"),
  "+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
t0<-Sys.time()
m<-tryCatch(inla(form,family="nbinomial",data=DD,E=DD$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),
  control.compute=list(waic=TRUE,config=FALSE),control.inla=list(control.vb=list(emergency=50))),error=function(e)NULL)
if(is.null(m))m<-inla(form,family="nbinomial",data=DD,E=DD$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),
  control.compute=list(waic=TRUE,config=FALSE),control.inla=list(control.vb=list(emergency=50),int.strategy="eb",strategy="gaussian"))
n<-nrow(G);ur<-m$summary.random$area[1:n,];pep<-sapply(m$marginals.random$area[1:n],function(mg)1-inla.pmarginal(0,mg))
OBS<-G$region%in%unique(DD$fbd_region)
rr<-data.frame(area=1:n,fbd_region=G$region,RR=round(exp(ur$mean),4),P_gt1=round(pep,4));rr$class<-ifelse(rr$P_gt1>0.95,"hotspot",ifelse(rr$P_gt1<0.05,"coldspot","neutral"));rr$class[!OBS]<-"unobserved"
write.csv(rr,file.path(OUT,sprintf("forced_%s_RR.csv",MODE)),row.names=FALSE)
hp<-m$summary.hyperpar;write.csv(data.frame(hyperpar=rownames(hp),round(hp[,c("mean","0.025quant","0.975quant")],4),forced=paste(FORCED,collapse=";"),WAIC=round(m$waic$waic,1),
  minutes=round(as.numeric(difftime(Sys.time(),t0,units="mins")),2)),file.path(OUT,sprintf("forced_%s_hyper.csv",MODE)),row.names=FALSE)
cat(sprintf("[98R] %s %s: phi %.3f · hot %d cold %d · %.1f min\n",TAG,MODE,hp["Phi for area","mean"],sum(rr$class=="hotspot"),sum(rr$class=="coldspot"),as.numeric(difftime(Sys.time(),t0,units="mins"))))
