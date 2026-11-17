# GKE node pool upgrade stalled

1. Check PodDisruptionBudgets with zero disruptions allowed.
2. GKE respects PDBs for up to an hour during a drain; fix the PDB or the unhealthy pods before that.
