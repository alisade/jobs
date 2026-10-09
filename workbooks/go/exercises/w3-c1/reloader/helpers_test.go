package reloader

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"
	"k8s.io/client-go/util/workqueue"
)

// harness runs a Controller against a fake clientset with real informers.
type harness struct {
	t       *testing.T
	client  *fake.Clientset
	factory informers.SharedInformerFactory
	ctrl    *Controller
	cancel  context.CancelFunc
	done    chan error
}

func fastOpts() Options {
	return Options{
		RateLimiter: workqueue.NewTypedItemExponentialFailureRateLimiter[string](time.Millisecond, 10*time.Millisecond),
		MaxRetries:  3,
		Logger:      slog.New(slog.NewTextHandler(io.Discard, nil)),
	}
}

// newHarness builds the controller; prepare can add reactors before start.
func newHarness(t *testing.T, opts Options, prepare func(*fake.Clientset), objs ...runtime.Object) *harness {
	t.Helper()
	client := fake.NewClientset(objs...)
	if prepare != nil {
		prepare(client)
	}
	factory := informers.NewSharedInformerFactory(client, 0)
	ctrl, err := NewController(client, factory, opts)
	if err != nil {
		t.Fatalf("NewController: %v", err)
	}
	return &harness{t: t, client: client, factory: factory, ctrl: ctrl}
}

// start starts informers and the controller with 2 workers.
func (h *harness) start() {
	ctx, cancel := context.WithCancel(context.Background())
	h.cancel = cancel
	h.done = make(chan error, 1)
	h.factory.Start(ctx.Done())
	go func() { h.done <- h.ctrl.Run(ctx, 2) }()
	h.t.Cleanup(func() {
		cancel()
		select {
		case <-h.done:
		case <-time.After(5 * time.Second):
		}
		h.factory.Shutdown()
	})
}

func (h *harness) deployment(ns, name string) *appsv1.Deployment {
	h.t.Helper()
	d, err := h.client.AppsV1().Deployments(ns).Get(context.Background(), name, metav1.GetOptions{})
	if err != nil {
		h.t.Fatalf("get deployment %s/%s: %v", ns, name, err)
	}
	return d
}

// eventually polls cond every 10ms for up to 5s.
func eventually(t *testing.T, msg string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatalf("timed out: %s", msg)
}

func countActions(c *fake.Clientset, verb, resource string) int {
	n := 0
	for _, a := range c.Actions() {
		if a.GetVerb() == verb && a.GetResource().Resource == resource {
			n++
		}
	}
	return n
}

var _ = k8stesting.PatchActionImpl{}

func configMap(ns, name string, watched bool, data map[string]string) *corev1.ConfigMap {
	cm := &corev1.ConfigMap{ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: name, Labels: map[string]string{}}, Data: data}
	if watched {
		cm.Labels[WatchLabel] = "true"
	}
	return cm
}

func deployment(ns, name string, refs string, tmplAnn map[string]string) *appsv1.Deployment {
	d := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: name, Annotations: map[string]string{}},
		Spec: appsv1.DeploymentSpec{
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": name}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": name}, Annotations: tmplAnn},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "app", Image: "ghcr.io/lumenpay/" + name + ":1.0"}}},
			},
		},
	}
	if refs != "" {
		d.Annotations[ReferenceAnnotation] = refs
	}
	return d
}
