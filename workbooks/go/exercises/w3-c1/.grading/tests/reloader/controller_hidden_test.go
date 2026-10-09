package reloader

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"
	"k8s.io/client-go/tools/cache"
)

var deployGR = schema.GroupResource{Group: "apps", Resource: "deployments"}

func TestHiddenIgnoresUnlabelledConfigMaps(t *testing.T) {
	cm := configMap("payments", "plain", false, map[string]string{"a": "1"})
	h := newHarness(t, fastOpts(), nil, cm, deployment("payments", "api", "plain", nil))
	h.start()
	time.Sleep(300 * time.Millisecond)
	if n := countActions(h.client, "patch", "deployments"); n != 0 {
		t.Fatalf("patched %d times for a ConfigMap without %s=true", n, WatchLabel)
	}
	// Direct handler calls must not enqueue either.
	h2 := newHarness(t, fastOpts(), nil)
	h2.ctrl.onConfigMapAdd(cm)
	h2.ctrl.onConfigMapUpdate(cm, cm.DeepCopy())
	h2.ctrl.onConfigMapDelete(cm)
	if h2.ctrl.queue.Len() != 0 {
		t.Fatalf("queue length %d after events for an unlabelled ConfigMap, want 0", h2.ctrl.queue.Len())
	}
}

func TestHiddenOnlyReferencingDeploymentsInSameNamespace(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	h := newHarness(t, fastOpts(), nil, cm,
		deployment("payments", "ledger-api", "other, ledger-config", nil),
		deployment("payments", "unrelated", "", nil),
		deployment("risk", "ledger-api", "ledger-config", nil),
	)
	h.start()
	key := HashAnnotationPrefix + "ledger-config"
	eventually(t, "payments/ledger-api annotated (reference list with spaces)", func() bool {
		return h.deployment("payments", "ledger-api").Spec.Template.Annotations[key] == HashConfigMap(cm)
	})
	time.Sleep(200 * time.Millisecond)
	if _, ok := h.deployment("payments", "unrelated").Spec.Template.Annotations[key]; ok {
		t.Fatal("annotated a Deployment that does not reference the ConfigMap")
	}
	if _, ok := h.deployment("risk", "ledger-api").Spec.Template.Annotations[key]; ok {
		t.Fatal("annotated a Deployment in another namespace")
	}
}

func TestHiddenIdempotentNoPatchWhenHashUnchanged(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	key := HashAnnotationPrefix + "ledger-config"
	d := deployment("payments", "ledger-api", "ledger-config", map[string]string{key: HashConfigMap(cm)})
	h := newHarness(t, fastOpts(), nil, cm, d)
	h.start()
	// Metadata-only change to the ConfigMap: content hash is the same.
	cm2 := cm.DeepCopy()
	cm2.Labels["team"] = "ledger"
	cm2.ResourceVersion = "5"
	if _, err := h.client.CoreV1().ConfigMaps("payments").Update(context.Background(), cm2, metav1.UpdateOptions{}); err != nil {
		t.Fatal(err)
	}
	time.Sleep(400 * time.Millisecond)
	if n := countActions(h.client, "patch", "deployments"); n != 0 {
		t.Fatalf("%d patches although the hash was already current; writes must be skipped when converged", n)
	}
}

func TestHiddenNoHotLoopAfterPatch(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	h := newHarness(t, fastOpts(), nil, cm, deployment("payments", "ledger-api", "ledger-config", nil))
	h.start()
	eventually(t, "first patch", func() bool { return countActions(h.client, "patch", "deployments") >= 1 })
	time.Sleep(500 * time.Millisecond)
	if n := countActions(h.client, "patch", "deployments"); n != 1 {
		t.Fatalf("%d patches for a single change; our own patch event must not cause another write", n)
	}
}

func TestHiddenUsesPatchNotUpdate(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	var patchType atomic.Value
	h := newHarness(t, fastOpts(), func(c *fake.Clientset) {
		c.PrependReactor("patch", "deployments", func(a k8stesting.Action) (bool, runtime.Object, error) {
			patchType.Store(a.(k8stesting.PatchAction).GetPatchType())
			return false, nil, nil
		})
	}, cm, deployment("payments", "ledger-api", "ledger-config", nil))
	h.start()
	eventually(t, "a patch", func() bool { return patchType.Load() != nil })
	pt := patchType.Load().(types.PatchType)
	if pt != types.MergePatchType && pt != types.StrategicMergePatchType && pt != types.ApplyPatchType {
		t.Fatalf("patch type %q; use a merge, strategic-merge or apply patch", pt)
	}
	if n := countActions(h.client, "update", "deployments"); n != 0 {
		t.Fatalf("%d Update calls on Deployments; a full Update races with other writers (conflicts, clobbering)", n)
	}
}

func TestHiddenNewDeploymentGetsCurrentHash(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	h := newHarness(t, fastOpts(), nil, cm)
	h.start()
	time.Sleep(100 * time.Millisecond)
	if _, err := h.client.AppsV1().Deployments("payments").Create(context.Background(),
		deployment("payments", "late", "ledger-config", nil), metav1.CreateOptions{}); err != nil {
		t.Fatal(err)
	}
	eventually(t, "a Deployment created later gets the hash", func() bool {
		return h.deployment("payments", "late").Spec.Template.Annotations[HashAnnotationPrefix+"ledger-config"] == HashConfigMap(cm)
	})
}

func TestHiddenDeleteRemovesAnnotation(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	key := HashAnnotationPrefix + "ledger-config"
	d := deployment("payments", "ledger-api", "ledger-config", map[string]string{key: HashConfigMap(cm), "keep": "me"})
	h := newHarness(t, fastOpts(), nil, cm, d)
	h.start()
	time.Sleep(200 * time.Millisecond)
	if err := h.client.CoreV1().ConfigMaps("payments").Delete(context.Background(), "ledger-config", metav1.DeleteOptions{}); err != nil {
		t.Fatal(err)
	}
	eventually(t, "hash annotation removed after the ConfigMap is deleted", func() bool {
		_, ok := h.deployment("payments", "ledger-api").Spec.Template.Annotations[key]
		return !ok
	})
	if h.deployment("payments", "ledger-api").Spec.Template.Annotations["keep"] != "me" {
		t.Fatal("other pod template annotations must be preserved")
	}
}

func TestHiddenDeleteHandlesTombstone(t *testing.T) {
	h := newHarness(t, fastOpts(), nil)
	cm := configMap("payments", "ledger-config", true, nil)
	h.ctrl.onConfigMapDelete(cache.DeletedFinalStateUnknown{Key: "payments/ledger-config", Obj: cm})
	if h.ctrl.queue.Len() != 1 {
		t.Fatalf("queue length %d after a DeletedFinalStateUnknown for a watched ConfigMap, want 1", h.ctrl.queue.Len())
	}
	k, _ := h.ctrl.queue.Get()
	if k != "payments/ledger-config" {
		t.Fatalf("key = %q, want payments/ledger-config", k)
	}
	h.ctrl.queue.Done(k)
	h.ctrl.onConfigMapDelete(cache.DeletedFinalStateUnknown{Key: "payments/plain", Obj: configMap("payments", "plain", false, nil)})
	h.ctrl.onConfigMapDelete("garbage")
	if h.ctrl.queue.Len() != 0 {
		t.Fatal("unwatched tombstones and unexpected types must be ignored, not enqueued or panicked on")
	}
}

func TestHiddenRetriesTransientErrorsThenForgets(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	var fails atomic.Int32
	h := newHarness(t, fastOpts(), func(c *fake.Clientset) {
		c.PrependReactor("patch", "deployments", func(a k8stesting.Action) (bool, runtime.Object, error) {
			if fails.Add(1) <= 2 {
				return true, nil, apierrors.NewServiceUnavailable("apiserver is shutting down")
			}
			return false, nil, nil
		})
	}, cm, deployment("payments", "ledger-api", "ledger-config", nil))
	h.start()
	eventually(t, "patch succeeds after 2 transient failures", func() bool {
		return h.deployment("payments", "ledger-api").Spec.Template.Annotations[HashAnnotationPrefix+"ledger-config"] != ""
	})
	eventually(t, "NumRequeues reset (Forget) after success", func() bool {
		return h.ctrl.queue.NumRequeues("payments/ledger-config") == 0
	})
}

func TestHiddenDropsAfterMaxRetries(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"a": "1"})
	var attempts atomic.Int32
	opts := fastOpts() // MaxRetries 3
	h := newHarness(t, opts, func(c *fake.Clientset) {
		c.PrependReactor("patch", "deployments", func(a k8stesting.Action) (bool, runtime.Object, error) {
			attempts.Add(1)
			return true, nil, apierrors.NewForbidden(deployGR, "ledger-api", errors.New("denied by admission policy"))
		})
	}, cm, deployment("payments", "ledger-api", "ledger-config", nil))
	h.start()
	eventually(t, "MaxRetries+1 attempts", func() bool { return attempts.Load() >= int32(opts.MaxRetries+1) })
	time.Sleep(300 * time.Millisecond)
	if got := attempts.Load(); got != int32(opts.MaxRetries+1) {
		t.Fatalf("%d patch attempts, want exactly %d (1 + MaxRetries) then drop", got, opts.MaxRetries+1)
	}
	if n := h.ctrl.queue.NumRequeues("payments/ledger-config"); n != 0 {
		t.Fatalf("NumRequeues = %d after dropping; call Forget so the rate limiter does not leak", n)
	}
}

func TestHiddenRunShutsDownCleanly(t *testing.T) {
	client := fake.NewClientset()
	factory := informers.NewSharedInformerFactory(client, 0)
	c, err := NewController(client, factory, fastOpts())
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	factory.Start(ctx.Done())
	done := make(chan error, 1)
	go func() { done <- c.Run(ctx, 3) }()
	time.Sleep(200 * time.Millisecond)
	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("Run returned %v on clean shutdown, want nil", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("Run did not return within 3s of ctx cancel")
	}
	if !c.queue.ShuttingDown() {
		t.Fatal("queue must be shut down when Run returns")
	}
	factory.Shutdown()
}

func TestHiddenRunReturnsErrCacheSyncWhenNeverSynced(t *testing.T) {
	client := fake.NewClientset()
	factory := informers.NewSharedInformerFactory(client, 0)
	c, err := NewController(client, factory, fastOpts())
	if err != nil {
		t.Fatal(err)
	}
	// factory deliberately NOT started: caches can never sync.
	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- c.Run(ctx, 1) }()
	select {
	case err := <-done:
		if !errors.Is(err, ErrCacheSync) {
			t.Fatalf("Run = %v, want ErrCacheSync", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("Run blocked although the caches can never sync")
	}
}

func TestHiddenHashCoversBinaryDataAndIsUnambiguous(t *testing.T) {
	a := &corev1.ConfigMap{Data: map[string]string{"ab": "c"}}
	b := &corev1.ConfigMap{Data: map[string]string{"a": "bc"}}
	if HashConfigMap(a) == HashConfigMap(b) {
		t.Fatal(`{"ab":"c"} and {"a":"bc"} must hash differently: delimit keys and values`)
	}
	c := &corev1.ConfigMap{BinaryData: map[string][]byte{"cert": {1, 2, 3}}}
	d := &corev1.ConfigMap{BinaryData: map[string][]byte{"cert": {1, 2, 4}}}
	if HashConfigMap(c) == HashConfigMap(d) {
		t.Fatal("BinaryData changes must change the hash")
	}
	big := &corev1.ConfigMap{Data: map[string]string{}}
	for i := range 50 {
		big.Data[string(rune('a'+i%26))+string(rune('A'+i/26))] = "v"
	}
	first := HashConfigMap(big)
	for range 20 {
		if HashConfigMap(big) != first {
			t.Fatal("hash depends on map iteration order")
		}
	}
	if len(first) != 64 {
		t.Fatalf("hash %q is not 64 hex chars (SHA-256)", first)
	}
	_ = appsv1.Deployment{}
}
