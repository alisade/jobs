package controller

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	"sigs.k8s.io/yaml"
)

// operatorSA is the identity the operator runs as in tenant-system.
const operatorSA = "system:serviceaccount:tenant-system:tenant-operator"

// Paths prepared by grade.sh: role.yaml is regenerated from the markers;
// role.committed.yaml is what the learner committed.
var (
	generatedRole = filepath.Join("..", "..", "config", "rbac", "role.yaml")
	committedRole = filepath.Join("..", "..", "config", "rbac", "role.committed.yaml")
)

func loadClusterRole(t *testing.T, path string) *rbacv1.ClusterRole {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	var cr rbacv1.ClusterRole
	if err := yaml.Unmarshal(bytes.TrimPrefix(raw, []byte("---\n")), &cr); err != nil {
		t.Fatalf("parse %s: %v", path, err)
	}
	if cr.Kind != "ClusterRole" || len(cr.Rules) == 0 {
		t.Fatalf("%s: expected a ClusterRole with rules", path)
	}
	return &cr
}

// operatorConfig creates a client-cert user named like the operator's SA and
// grants it exactly the ClusterRole generated from the kubebuilder markers.
func operatorConfig(t *testing.T) *rest.Config {
	t.Helper()
	ctx := context.Background()
	cr := loadClusterRole(t, generatedRole)
	cr.Name = "tenant-operator-under-test"
	cr.ResourceVersion = ""
	if err := adminClient.Create(ctx, cr); err != nil && !apierrors.IsAlreadyExists(err) {
		t.Fatalf("create clusterrole: %v", err)
	}
	crb := &rbacv1.ClusterRoleBinding{
		ObjectMeta: metav1.ObjectMeta{Name: "tenant-operator-under-test"},
		RoleRef:    rbacv1.RoleRef{APIGroup: "rbac.authorization.k8s.io", Kind: "ClusterRole", Name: cr.Name},
		Subjects:   []rbacv1.Subject{{Kind: "User", APIGroup: "rbac.authorization.k8s.io", Name: operatorSA}},
	}
	if err := adminClient.Create(ctx, crb); err != nil && !apierrors.IsAlreadyExists(err) {
		t.Fatalf("create clusterrolebinding: %v", err)
	}
	user, err := testEnv.AddUser(envtest.User{
		Name:   operatorSA,
		Groups: []string{"system:serviceaccounts", "system:serviceaccounts:tenant-system", "system:authenticated"},
	}, nil)
	if err != nil {
		t.Fatalf("add user: %v", err)
	}
	return user.Config()
}

func TestHiddenReconcilesAsOperatorServiceAccount(t *testing.T) {
	startManager(t, operatorConfig(t))
	ns := newNamespace(t, "sa-reconcile")
	tn := newTenant(ns, "churn-model")
	if err := adminClient.Create(context.Background(), tn); err != nil {
		t.Fatal(err)
	}
	waitFor(t, 30*time.Second, "Tenant Ready=True while running with the generated RBAC only", func() bool {
		return tenantReady(t, adminClient, client.ObjectKeyFromObject(tn))
	})
	var q corev1.ResourceQuota
	if err := adminClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: QuotaName(tn)}, &q); err != nil {
		t.Fatalf("resourcequota not created: %v", err)
	}
}

func TestHiddenRestoresDeletedSecretAsOperator(t *testing.T) {
	startManager(t, operatorConfig(t))
	ns := newNamespace(t, "sa-drift")
	tn := newTenant(ns, "pricing")
	ctx := context.Background()
	if err := adminClient.Create(ctx, tn); err != nil {
		t.Fatal(err)
	}
	key := client.ObjectKey{Namespace: ns, Name: SecretName(tn)}
	var s corev1.Secret
	waitFor(t, 30*time.Second, "storage Secret created", func() bool { return adminClient.Get(ctx, key, &s) == nil })
	uid := s.UID
	if err := adminClient.Delete(ctx, &s); err != nil {
		t.Fatal(err)
	}
	// Only an Owns()/watch on Secrets brings it back: the Tenant itself did not change.
	waitFor(t, 20*time.Second, "deleted storage Secret restored by the owned-object watch (SEC-2291)", func() bool {
		var again corev1.Secret
		return adminClient.Get(ctx, key, &again) == nil && again.UID != uid
	})
}

func TestHiddenGeneratedRoleIsLeastPrivilege(t *testing.T) {
	cr := loadClusterRole(t, generatedRole)
	var secretVerbs []string
	for _, r := range cr.Rules {
		for _, field := range [][]string{r.APIGroups, r.Resources, r.Verbs} {
			if slices.Contains(field, "*") {
				t.Fatalf("wildcard in rule %+v: grant exact groups/resources/verbs", r)
			}
		}
		for _, v := range r.Verbs {
			if v == "escalate" || v == "bind" || v == "impersonate" {
				t.Fatalf("privilege-escalation verb %q in rule %+v", v, r)
			}
		}
		if len(r.NonResourceURLs) > 0 {
			t.Fatalf("operator does not need nonResourceURLs: %+v", r)
		}
		if slices.Contains(r.APIGroups, "") && slices.Contains(r.Resources, "secrets") {
			secretVerbs = append(secretVerbs, r.Verbs...)
		}
		for _, res := range r.Resources {
			switch res {
			case "clusterroles", "clusterrolebindings", "roles", "rolebindings", "serviceaccounts/token", "nodes", "pods/exec":
				t.Fatalf("operator should not be granted %q", res)
			}
		}
	}
	for _, v := range []string{"get", "list", "watch"} {
		if !slices.Contains(secretVerbs, v) {
			t.Fatalf("secrets verbs %v: an owned-object informer needs %q", secretVerbs, v)
		}
	}
	// No hand-written cluster-admin binding smuggled into the manifests.
	entries, _ := os.ReadDir(filepath.Join("..", "..", "config", "rbac"))
	for _, e := range entries {
		raw, _ := os.ReadFile(filepath.Join("..", "..", "config", "rbac", e.Name()))
		if strings.Contains(string(raw), "name: cluster-admin") {
			t.Fatalf("config/rbac/%s binds cluster-admin", e.Name())
		}
	}
}

func TestHiddenCommittedRoleMatchesMarkers(t *testing.T) {
	gen, err := os.ReadFile(generatedRole)
	if err != nil {
		t.Fatal(err)
	}
	committed, err := os.ReadFile(committedRole)
	if err != nil {
		t.Fatalf("no committed config/rbac/role.yaml: %v", err)
	}
	if !bytes.Equal(bytes.TrimSpace(gen), bytes.TrimSpace(committed)) {
		t.Fatal("config/rbac/role.yaml is stale: change the +kubebuilder:rbac markers, then run `make manifests` and commit the result (CI ships the YAML, not the markers)")
	}
}
