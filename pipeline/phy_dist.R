# Patristic distances among our species.
#   Mammalia: cophenetic on a dated tree (MDD tips) pruned to matched
#             names -> REAL phylogenetic distance (Myr). Tree path via
#             env WILDSEEK_MAMMAL_TREE, default data/v6_point.nwk.
#   Aves:     no tree yet -> phy_source="proxy" rows are left to the
#             GBIF taxonomic fallback in dist_frame.py.
# Output: phy_dist.csv (item1,item2,phylo_distance,source)

library(ape)

TREE <- Sys.getenv("WILDSEEK_MAMMAL_TREE", "data/v6_point.nwk")
W <- read.csv("data/species_winner.csv", stringsAsFactors = FALSE)
W$u <- gsub(" ", "_", W$species)

tr <- read.tree(TREE)
keep <- intersect(W$u, tr$tip.label)
cat("matched on v6 tree:", length(keep), "\n")

tr <- keep.tip(tr, keep)
d <- cophenetic.phylo(tr)
idx <- which(upper.tri(d), arr.ind = TRUE)
out <- data.frame(
  item1 = rownames(d)[idx[, 1]],
  item2 = colnames(d)[idx[, 2]],
  phylo_distance = d[idx],
  source = "v6_dated")
out$item1 <- gsub("_", " ", out$item1)
out$item2 <- gsub("_", " ", out$item2)
write.csv(out, "data/phy_dist.csv", row.names = FALSE)
cat("pairs:", nrow(out), "median d:", median(out$phylo_distance), "\n")
