package sink

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"slices"
	"sync"
	"testing"
	"time"

	"github.com/twmb/franz-go/pkg/kerr"
	"github.com/twmb/franz-go/pkg/kfake"
	"github.com/twmb/franz-go/pkg/kgo"
	appsv1 "k8s.io/api/apps/v1"
	autoscalingv2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	"k8s.io/apimachinery/pkg/labels"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/yaml"
)

const manifestPath = "../../deploy/audit-sink.yaml"

// ---------- config ----------

func TestHiddenInstanceIDFallsBackToPodName(t *testing.T) {
	c, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": "b:1", "POD_NAME": "audit-sink-2"}))
	if err != nil {
		t.Fatalf("POD_NAME should be enough to identify the replica: %v", err)
	}
	if c.InstanceID != "audit-sink-2" {
		t.Fatalf("InstanceID = %q, want audit-sink-2", c.InstanceID)
	}
}

func TestHiddenExplicitInstanceIDWins(t *testing.T) {
	c, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": "b:1", "POD_NAME": "audit-sink-2", "GROUP_INSTANCE_ID": "custom-2"}))
	if err != nil || c.InstanceID != "custom-2" {
		t.Fatalf("GROUP_INSTANCE_ID must take precedence: %q %v", c.InstanceID, err)
	}
}

func TestHiddenNoConstantInstanceIDFallback(t *testing.T) {
	c, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": "b:1"}))
	if err == nil {
		t.Fatalf("static membership with no per-replica identity must be a config error, got InstanceID=%q", c.InstanceID)
	}
}

func TestHiddenStaticMembershipCanBeDisabled(t *testing.T) {
	cluster := kfake.MustCluster(kfake.NumBrokers(1))
	defer cluster.Close()
	c, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": cluster.ListenAddrs()[0], "KAFKA_STATIC_MEMBERSHIP": "false"}))
	if err != nil {
		t.Fatalf("dynamic membership needs no instance id: %v", err)
	}
	cl, err := kgo.NewClient(c.Opts()...)
	if err != nil {
		t.Fatal(err)
	}
	defer cl.Close()
	if vs := cl.OptValues(kgo.InstanceID); len(vs) == 2 && vs[1] == true {
		t.Fatalf("kgo.InstanceID set to %v with static membership disabled", vs[0])
	}
}

func TestHiddenOptsCarryInstanceID(t *testing.T) {
	cluster := kfake.MustCluster(kfake.NumBrokers(1))
	defer cluster.Close()
	c, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": cluster.ListenAddrs()[0], "POD_NAME": "audit-sink-1"}))
	if err != nil {
		t.Fatal(err)
	}
	cl, err := kgo.NewClient(c.Opts()...)
	if err != nil {
		t.Fatal(err)
	}
	defer cl.Close()
	if vs := cl.OptValues(kgo.InstanceID); len(vs) != 2 || vs[0] != "audit-sink-1" || vs[1] != true {
		t.Fatalf("client group.instance.id = %v, want audit-sink-1", vs)
	}
}

// ---------- manifest ----------

type workload struct {
	kind, name, ns string
	replicas       int32
	tmpl           corev1.PodTemplateSpec
	hpa            *autoscalingv2.HorizontalPodAutoscaler
	pdb            *policyv1.PodDisruptionBudget
}

func loadManifest(t *testing.T) workload {
	t.Helper()
	raw, err := os.ReadFile(manifestPath)
	if err != nil {
		t.Fatalf("read %s: %v", manifestPath, err)
	}
	var w workload
	found := 0
	for _, doc := range bytes.Split(raw, []byte("\n---")) {
		var tm metav1.TypeMeta
		if yaml.Unmarshal(doc, &tm) != nil {
			continue
		}
		switch tm.Kind {
		case "Deployment":
			var d appsv1.Deployment
			if err := yaml.UnmarshalStrict(doc, &d); err != nil {
				t.Fatalf("Deployment does not parse strictly: %v", err)
			}
			if d.Name != "audit-sink" {
				continue
			}
			found++
			w.kind, w.name, w.ns, w.tmpl, w.replicas = "Deployment", d.Name, d.Namespace, d.Spec.Template, 1
			if d.Spec.Replicas != nil {
				w.replicas = *d.Spec.Replicas
			}
		case "StatefulSet":
			var s appsv1.StatefulSet
			if err := yaml.UnmarshalStrict(doc, &s); err != nil {
				t.Fatalf("StatefulSet does not parse strictly: %v", err)
			}
			if s.Name != "audit-sink" {
				continue
			}
			found++
			w.kind, w.name, w.ns, w.tmpl, w.replicas = "StatefulSet", s.Name, s.Namespace, s.Spec.Template, 1
			if s.Spec.Replicas != nil {
				w.replicas = *s.Spec.Replicas
			}
		case "HorizontalPodAutoscaler":
			var h autoscalingv2.HorizontalPodAutoscaler
			if err := yaml.UnmarshalStrict(doc, &h); err != nil {
				t.Fatalf("HPA does not parse strictly: %v", err)
			}
			w.hpa = &h
		case "PodDisruptionBudget":
			var p policyv1.PodDisruptionBudget
			if err := yaml.UnmarshalStrict(doc, &p); err != nil {
				t.Fatalf("PDB does not parse strictly: %v", err)
			}
			w.pdb = &p
		}
	}
	if found != 1 {
		t.Fatalf("want exactly one audit-sink Deployment or StatefulSet, found %d", found)
	}
	return w
}

// pods resolves env per replica the way the kubelet would. rollout changes the
// generated names of Deployment pods (new ReplicaSet hash + random suffix).
func (w workload) pods(rollout int) []map[string]string {
	var out []map[string]string
	for i := 0; i < int(w.replicas); i++ {
		pod := fmt.Sprintf("%s-%d", w.name, i)
		if w.kind == "Deployment" {
			pod = fmt.Sprintf("%s-%d%07d-%05d", w.name, rollout, 7919*rollout, 104729*(i+1)*rollout%99991)
		}
		env := map[string]string{}
		for _, c := range w.tmpl.Spec.Containers {
			if c.Name != "audit-sink" {
				continue
			}
			for _, e := range c.Env {
				switch {
				case e.ValueFrom == nil:
					env[e.Name] = e.Value
				case e.ValueFrom.FieldRef != nil && e.ValueFrom.FieldRef.FieldPath == "metadata.name":
					env[e.Name] = pod
				case e.ValueFrom.FieldRef != nil && e.ValueFrom.FieldRef.FieldPath == "metadata.namespace":
					env[e.Name] = w.ns
				}
			}
		}
		out = append(out, env)
	}
	return out
}

func instanceIDs(t *testing.T, w workload, rollout int) []string {
	t.Helper()
	var ids []string
	for _, env := range w.pods(rollout) {
		env["KAFKA_BROKERS"] = "b:1"
		c, err := FromEnv(envMap(env))
		if err != nil {
			t.Fatalf("replica config from manifest fails: %v", err)
		}
		if !c.StaticMembership || c.InstanceID == "" {
			t.Fatal("static membership was turned off: PR #412's goal (no rebalance on every rolling deploy) must be kept")
		}
		ids = append(ids, c.InstanceID)
	}
	return ids
}

func TestHiddenManifestReplicasHaveDistinctInstanceIDs(t *testing.T) {
	w := loadManifest(t)
	if w.replicas < 3 {
		t.Fatalf("replicas = %d, want >= 3 (capacity was not the problem)", w.replicas)
	}
	ids := instanceIDs(t, w, 1)
	seen := map[string]bool{}
	for _, id := range ids {
		if seen[id] {
			t.Fatalf("replicas share group.instance.id %q: they fence each other (ids=%v)", id, ids)
		}
		seen[id] = true
	}
}

func TestHiddenManifestInstanceIDsStableAcrossRollouts(t *testing.T) {
	w := loadManifest(t)
	a, b := instanceIDs(t, w, 1), instanceIDs(t, w, 2)
	if !slices.Equal(a, b) {
		t.Fatalf("group.instance.id changes on every rollout (%v -> %v): the old static members linger until "+
			"session.timeout and their partitions stall; static membership needs stable identities (StatefulSet ordinals)", a, b)
	}
}

func TestHiddenHPATargetsTheWorkload(t *testing.T) {
	w := loadManifest(t)
	if w.hpa == nil {
		t.Skip("no HPA in manifest")
	}
	ref := w.hpa.Spec.ScaleTargetRef
	if ref.Kind != w.kind || ref.Name != w.name {
		t.Fatalf("HPA scaleTargetRef = %s/%s but the workload is %s/%s", ref.Kind, ref.Name, w.kind, w.name)
	}
	if w.hpa.Spec.MinReplicas == nil || *w.hpa.Spec.MinReplicas < 3 {
		t.Fatal("HPA minReplicas must stay >= 3")
	}
}

func TestHiddenPDBStillSelectsPods(t *testing.T) {
	w := loadManifest(t)
	if w.pdb == nil {
		t.Fatal("keep the PodDisruptionBudget")
	}
	sel, err := metav1.LabelSelectorAsSelector(w.pdb.Spec.Selector)
	if err != nil || sel.Empty() || !sel.Matches(labels.Set(w.tmpl.Labels)) {
		t.Fatalf("PDB selector %v does not select the pod template labels %v", w.pdb.Spec.Selector, w.tmpl.Labels)
	}
}

// ---------- end to end against an in-process Kafka ----------

func TestHiddenGroupIsStableWithManifestReplicas(t *testing.T) {
	w := loadManifest(t)
	cluster := kfake.MustCluster(kfake.NumBrokers(1), kfake.SeedTopics(6, "agent.audit"))
	defer cluster.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 6*time.Second)
	defer cancel()

	var mu sync.Mutex
	owned := map[int][]int32{}
	fenced := 0
	var wg sync.WaitGroup
	for i, env := range w.pods(1) {
		env["KAFKA_BROKERS"] = cluster.ListenAddrs()[0]
		c, err := FromEnv(envMap(env))
		if err != nil {
			t.Fatalf("replica %d config: %v", i, err)
		}
		cl, err := kgo.NewClient(append(c.Opts(),
			kgo.OnPartitionsAssigned(func(_ context.Context, _ *kgo.Client, m map[string][]int32) {
				mu.Lock()
				owned[i] = append(owned[i], m["agent.audit"]...)
				mu.Unlock()
			}),
			kgo.OnPartitionsRevoked(func(_ context.Context, _ *kgo.Client, m map[string][]int32) {
				mu.Lock()
				owned[i] = slices.DeleteFunc(owned[i], func(p int32) bool { return slices.Contains(m["agent.audit"], p) })
				mu.Unlock()
			}),
			kgo.OnPartitionsLost(func(_ context.Context, _ *kgo.Client, m map[string][]int32) {
				mu.Lock()
				owned[i] = nil
				mu.Unlock()
			}),
		)...)
		if err != nil {
			t.Fatal(err)
		}
		wg.Add(1)
		go func() {
			defer wg.Done()
			defer cl.Close()
			for ctx.Err() == nil {
				cl.PollFetches(ctx).EachError(func(_ string, _ int32, err error) {
					if errors.Is(err, kerr.FencedInstanceID) {
						mu.Lock()
						fenced++
						mu.Unlock()
					}
				})
			}
		}()
	}
	time.Sleep(5 * time.Second)
	mu.Lock()
	snapshot := map[int][]int32{}
	for k, v := range owned {
		snapshot[k] = slices.Clone(v)
	}
	f := fenced
	mu.Unlock()
	cancel()
	wg.Wait()

	if f > 0 {
		t.Fatalf("%d FENCED_INSTANCE_ID errors with the manifest's replicas", f)
	}
	var all []int32
	for i := 0; i < int(w.replicas); i++ {
		if len(snapshot[i]) == 0 {
			t.Fatalf("replica %d owns no partitions after 5s: %v", i, snapshot)
		}
		all = append(all, snapshot[i]...)
	}
	slices.Sort(all)
	if !slices.Equal(all, []int32{0, 1, 2, 3, 4, 5}) {
		t.Fatalf("partitions must be owned exactly once across replicas, got %v", snapshot)
	}
}
