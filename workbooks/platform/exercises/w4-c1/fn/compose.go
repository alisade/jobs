package fn

// Size to Cloud SQL machine tier, and the version names the provider expects.
var tiers = map[string]string{
	"small":  "db-custom-1-3840",
	"medium": "db-custom-2-7680",
	"large":  "db-custom-4-15360",
}

var versions = map[string]string{
	"postgres-15": "POSTGRES_15",
	"postgres-16": "POSTGRES_16",
}

// Compose turns an AppDatabase XR into its desired composed resources.
//
// The full contract is in README.md ("Composition contract"). In short:
//   - Validate first. Bad input returns Result{Fatal: "<field path>: <what is wrong>"} and no
//     resources. Never panic.
//   - Desired resources, in this order: DatabaseInstance <xr>-pg, (large only) DatabaseInstance
//     <xr>-pg-replica, Database <xr>-db, User <xr>-user.
//   - Every resource: APIVersion MRAPIVersion, the XR's namespace, labels LabelComposite and
//     LabelTeam only, the deletion policy (default "Delete") and the provider config reference
//     (default ClusterProviderConfig "default", unless spec.providerConfigRef overrides it).
//   - The User writes its connection secret <xr>-conn.
func Compose(xr XR) Result {
	// TODO: validate the XR (namespace, name, team, size, version, deletionPolicy,
	// providerConfigRef) and return Result{Fatal: ...} on the first problem.

	// TODO: build the desired resources described above and in README.md.
	_ = tiers
	_ = versions
	return Result{}
}
