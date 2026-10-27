#!/bin/bash
#SBATCH --job-name=inst_xnicher
#SBATCH --partition=sixhour
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --output=/beegfs/a474r867/meta-hack/logs/install_xnicher_%j.log
if [ ! -d /beegfs/a474r867 ]; then exit 53; fi
export R_LIBS=/beegfs/a474r867/rlib_442
mkdir -p "$R_LIBS"
SIF=/home/a474r867/geospatial-rserver/xsdm_latest.sif
SRC=/beegfs/a474r867/rlib_442/srcpkgs
apptainer exec --cleanenv --env R_LIBS="$R_LIBS" "$SIF" R --slave -e "
lib <- Sys.getenv('R_LIBS'); src <- '$SRC'
pkgs <- c('Rcpp','RcppEigen','RcppParallel','checkmate','xnicher')
for (p in pkgs) {
  if (!requireNamespace(p, quietly=TRUE)) {
    f <- list.files(src, pattern=paste0('^',p,'_'), full.names=TRUE)[1]
    cat('installing', p, 'from', basename(f), '\n')
    install.packages(f, lib=lib, repos=NULL, type='source', Ncpus=2)
  } else cat(p, 'already present\n')
}
stopifnot(requireNamespace('xnicher', quietly=TRUE))
cat('OK xnicher', as.character(packageVersion('xnicher')), '\n')
"
