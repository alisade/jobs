package fn

import (
	"fmt"
	"regexp"
	"strings"
)

var tiers = map[string]string{
	"small":  "db-custom-1-3840",
	"medium": "db-custom-2-7680",
	"large":  "db-custom-4-15360",
}

var versions = map[string]string{
	"postgres-15": "POSTGRES_15",
	"postgres-16": "POSTGRES_16",
}

var teamRE = regexp.MustCompile(`^[a-z][a-z0-9-]{0,29}$`)

// Compose turns an AppDatabase XR into its desired composed resources.
func Compose(xr XR) Result {
	if msg := validate(xr); msg != "" {
		return Result{Fatal: msg}
	}
	s := xr.Spec
	name, ns := xr.Metadata.Name, xr.Metadata.Namespace
	region := s.Region
	if region == "" {
		region = DefaultRegion
	}
	policy := s.DeletionPolicy
	if policy == "" {
		policy = "Delete"
	}
	pc := ProviderConfigRef{Kind: "ClusterProviderConfig", Name: "default"}
	if s.ProviderConfigRef != nil {
		pc = *s.ProviderConfigRef
		if pc.Kind == "" {
			pc.Kind = "ClusterProviderConfig"
		}
	}
	avail := "ZONAL"
	if s.Size == "large" {
		avail = "REGIONAL"
	}
	mk := func(kind, rname string, fp map[string]string) Resource {
		return Resource{
			APIVersion:        MRAPIVersion,
			Kind:              kind,
			Metadata:          ObjectMeta{Name: rname, Namespace: ns, Labels: map[string]string{LabelComposite: name, LabelTeam: s.Team}},
			ForProvider:       fp,
			DeletionPolicy:    policy,
			ProviderConfigRef: pc,
		}
	}
	inst := name + "-pg"
	out := []Resource{mk(KindInstance, inst, map[string]string{
		"databaseVersion": versions[s.Version], "tier": tiers[s.Size], "region": region, "availabilityType": avail,
	})}
	if s.Size == "large" {
		out = append(out, mk(KindInstance, inst+"-replica", map[string]string{
			"databaseVersion": versions[s.Version], "tier": tiers[s.Size], "region": region, "masterInstanceName": inst,
		}))
	}
	out = append(out, mk(KindDatabase, name+"-db", map[string]string{
		"instance": inst, "name": strings.ReplaceAll(name, "-", "_"), "charset": "UTF8",
	}))
	user := mk(KindUser, name+"-user", map[string]string{"instance": inst, "name": name + "-app"})
	user.WriteConnectionSecretToRef = &SecretRef{Name: name + "-conn"}
	out = append(out, user)
	return Result{Desired: out}
}

func validate(xr XR) string {
	s := xr.Spec
	if xr.Metadata.Namespace == "" {
		return "metadata.namespace: AppDatabase is namespaced; create it in your team namespace"
	}
	if xr.Metadata.Name == "" {
		return "metadata.name: required"
	}
	if !teamRE.MatchString(s.Team) {
		return fmt.Sprintf("spec.team: %q is not a lower-case DNS label", s.Team)
	}
	if _, ok := tiers[s.Size]; !ok {
		return fmt.Sprintf("spec.size: unsupported value %q (want small, medium, large)", s.Size)
	}
	if _, ok := versions[s.Version]; !ok {
		return fmt.Sprintf("spec.version: unsupported value %q (want postgres-15, postgres-16)", s.Version)
	}
	switch s.DeletionPolicy {
	case "", "Delete", "Orphan":
	default:
		return fmt.Sprintf("spec.deletionPolicy: unsupported value %q (want Delete or Orphan)", s.DeletionPolicy)
	}
	if p := s.ProviderConfigRef; p != nil {
		if p.Name == "" {
			return "spec.providerConfigRef.name: required when providerConfigRef is set"
		}
		if p.Kind != "" && p.Kind != "ProviderConfig" && p.Kind != "ClusterProviderConfig" {
			return fmt.Sprintf("spec.providerConfigRef.kind: unsupported value %q", p.Kind)
		}
	}
	return ""
}
