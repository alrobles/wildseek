# Subsampling experiment runner — one SLURM array task = a slice of tasks.
#
# Same likelihood/transform/optimizer settings as the campaign
# (xnicher_run.R): Box-Cox(prec, lambda on env_m) -> z-score by env_m
# moments -> optimize_niche(presence_only). The ONLY difference is the
# occurrence sample: full env_occ (is_full) vs n_level rows drawn with
# the task seed. opt_seed is recomputed with the campaign scheme so
# full-n refits must reproduce the catalog AIC.
#
# Usage: Rscript subsample_run.R <tasks.parquet> <shard> <n_shards> [num_starts]
# Output: $WILDSEEK_BEEG/subsample_v1/fits/fits_<shard>.csv

suppressMessages({
  library(duckdb); library(DBI); library(xnicher)
})

args <- commandArgs(trailingOnly = TRUE)
tasks_path <- args[1]
shard      <- as.integer(args[2])
n_shards   <- as.integer(args[3])
n_starts   <- if (length(args) >= 4) as.integer(args[4]) else 60L

OUT <- Sys.getenv("WILDSEEK_BEEG", ".")
RUN <- file.path(OUT, "subsample_v1")
DOM <- Sys.getenv("WILDSEEK_DOMAIN", "conus")
SUF <- ifelse(DOM == "conus", "", paste0("_", DOM))

con <- dbConnect(duckdb())
dbExecute(con, "PRAGMA threads=4")

tasks <- dbGetQuery(con, sprintf(
  "select * from '%s' where task_id %% %d = %d order by task_id",
  tasks_path, n_shards, shard))
cat("shard", shard, "tasks:", nrow(tasks), "\n")

bc_lambda <- function(x, eps = NULL) {
  if (is.null(eps)) eps <- min(x[x > 0], na.rm = TRUE) / 2
  if (!is.finite(eps) || eps <= 0) eps <- 1e-3
  x <- x + eps
  lx <- log(x); m <- mean(lx)
  f <- function(l) {
    z <- if (abs(l) < 1e-8) lx else (x^l - 1) / l
    v <- var(z)
    if (!is.finite(v) || v <= 0) return(Inf)
    -0.5 * length(z) * log(v) + (l - 1) * sum(lx)
  }
  opt <- optimize(f, c(-2, 2), maximum = TRUE)
  list(lambda = opt$maximum, eps = eps)
}
bc <- function(x, lam, eps) if (abs(lam) < 1e-8) log(x + eps) else ((x + eps)^lam - 1) / lam

bios <- paste0("bio", sprintf("%02d", 1:19))
res <- list(); k <- 0L; skipped <- 0L
t00 <- Sys.time()
for (ti in seq_len(nrow(tasks))) {
  t <- tasks[ti, ]
  cls <- if (t$class == "Aves") "aves" else "mammalia"
  occ <- tryCatch(dbGetQuery(con, sprintf(
    "select %s from '%s/env_occ_%s.parquet' where specieskey=%d",
    paste(bios, collapse = ","), OUT, cls, t$specieskey)),
    error = function(e) NULL)
  if (is.null(occ)) { skipped <- skipped + 1L; next }
  if (!isTRUE(t$is_full) && nrow(occ) < t$n_level) {
    skipped <- skipped + 1L; next  # selection guarantees n; this is drift
  }
  oo_full <- occ
  if (!isTRUE(t$is_full)) {
    set.seed(t$seed)
    occ <- occ[sample(nrow(occ), t$n_level), , drop = FALSE]
  }
  ecos <- dbGetQuery(con, sprintf(
    "select distinct eco_id from '%s/m_ecoregions.parquet' where specieskey=%d",
    OUT, t$specieskey))$eco_id
  if (length(ecos) == 0) { skipped <- skipped + 1L; next }
  m <- dbGetQuery(con, sprintf(
    "select %s from '%s/env_normals_96_25.parquet' where eco_id in (%s)",
    paste(bios, collapse = ","), OUT, paste(ecos, collapse = ",")))
  if (nrow(m) < 50) { skipped <- skipped + 1L; next }
  if (nrow(m) > 30000) m <- m[sample(nrow(m), 30000), ]

  tv <- t$temp; pv <- t$prec
  l <- bc_lambda(m[[pv]])
  mo <- bc(m[[pv]], l$lambda, l$eps); oo <- bc(occ[[pv]], l$lambda, l$eps)
  z <- function(v, a) (a - mean(v)) / sd(v)
  em <- cbind(z(m[[tv]], m[[tv]]), z(mo, mo))
  eo <- cbind(z(m[[tv]], occ[[tv]]), z(mo, oo))
  colnames(em) <- colnames(eo) <- c(tv, pv)
  if (any(!is.finite(eo))) { skipped <- skipped + 1L; next }

  opt_seed <- (t$specieskey %% 1e6) * 89 + t$pair_idx + 1L
  t0 <- Sys.time()
  fit <- tryCatch(
    optimize_niche(eo, em, likelihood = "presence_only",
                   num_starts = n_starts, seed = opt_seed),
    error = function(e) NULL)
  if (is.null(fit)) { skipped <- skipped + 1L; next }
  as_ <- assess(fit)
  ms <- xnicher:::.recover_mu_sigma(fit)
  ll <- as.numeric(logLik(fit)); df <- attr(logLik(fit), "df")
  k <- k + 1L
  res[[k]] <- data.frame(
    task_id = t$task_id, specieskey = t$specieskey, temp = tv, prec = pv,
    pair_idx = t$pair_idx, n_level = t$n_level, rep = t$rep,
    seed = t$seed, is_full = isTRUE(t$is_full), n_actual = nrow(occ),
    mu1 = ms$mu[1], mu2 = ms$mu[2],
    s11 = ms$Sigma[1, 1], s12 = ms$Sigma[1, 2], s22 = ms$Sigma[2, 2],
    logdet = as.numeric(determinant(ms$Sigma, logarithm = TRUE)$modulus),
    aic = -2 * ll + 2 * df, bic = -2 * ll + log(nobs(fit)) * df,
    loglik = ll, nobs = nobs(fit), flag = as_$flag,
    n_conv = as_$n_converged, rel_gap = as_$rel_gap,
    wall_s = as.numeric(difftime(Sys.time(), t0, units = "secs")))
  if (ti %% 200 == 0) cat("task", ti, "/", nrow(tasks),
    round(difftime(Sys.time(), t00, units = "mins"), 1), "min\n", flush = TRUE)
}
ans <- if (k > 0) do.call(rbind, res) else data.frame()
fn <- sprintf("%s/fits/fits_%04d.csv", RUN, shard)
dir.create(dirname(fn), showWarnings = FALSE, recursive = TRUE)
write.csv(ans, fn, row.names = FALSE)
cat("wrote", fn, nrow(ans), "rows | skipped", skipped, "\n")
