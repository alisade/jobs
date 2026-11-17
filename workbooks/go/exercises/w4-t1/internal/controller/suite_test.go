package controller

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	. "github.com/onsi/gomega"
	"go.uber.org/zap/zapcore"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	crmetrics "sigs.k8s.io/controller-runtime/pkg/metrics"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

// Shared envtest fixture. One API server and one manager for the whole package;
// every test works in its own namespace.
var (
	k8sClient  client.Client
	testScheme = runtime.NewScheme()
	reconciler *MCPServerReconciler
)

const (
	timeout  = 10 * time.Second
	interval = 100 * time.Millisecond
)

func TestMain(m *testing.M) {
	os.Exit(runSuite(m))
}

func runSuite(m *testing.M) int {
	if os.Getenv("KUBEBUILDER_ASSETS") == "" {
		fmt.Fprintln(os.Stderr, "KUBEBUILDER_ASSETS is not set: run tests via `make test`")
		return 1
	}
	logf.SetLogger(zap.New(zap.WriteTo(os.Stderr), zap.UseDevMode(true), zap.Level(zapLevel())))

	_ = clientgoscheme.AddToScheme(testScheme)
	_ = agentsv1alpha1.AddToScheme(testScheme)

	env := &envtest.Environment{
		CRDDirectoryPaths:     []string{filepath.Join("..", "..", "config", "crd", "bases")},
		ErrorIfCRDPathMissing: true,
	}
	cfg, err := env.Start()
	if err != nil {
		fmt.Fprintln(os.Stderr, "start envtest:", err)
		return 1
	}
	defer func() { _ = env.Stop() }()

	k8sClient, err = client.New(cfg, client.Options{Scheme: testScheme})
	if err != nil {
		fmt.Fprintln(os.Stderr, "client:", err)
		return 1
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	mgr, err := ctrl.NewManager(cfg, ctrl.Options{
		Scheme:  testScheme,
		Metrics: metricsserver.Options{BindAddress: "0"},
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, "manager:", err)
		return 1
	}
	reconciler = &MCPServerReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}
	if err := reconciler.SetupWithManager(mgr); err != nil {
		fmt.Fprintln(os.Stderr, "setup controller:", err)
		return 1
	}
	go func() {
		if err := mgr.Start(ctx); err != nil {
			fmt.Fprintln(os.Stderr, "manager stopped:", err)
		}
	}()
	return m.Run()
}

func zapLevel() zapcore.Level {
	if os.Getenv("TEST_VERBOSE") != "" {
		return zapcore.DebugLevel
	}
	return zapcore.ErrorLevel
}

// newNamespace creates a uniquely named namespace for one test.
func newNamespace(t *testing.T) string {
	t.Helper()
	ns := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{GenerateName: "mcp-test-"}}
	if err := k8sClient.Create(context.Background(), ns); err != nil {
		t.Fatalf("create namespace: %v", err)
	}
	return ns.Name
}

// newMCPServer returns an MCPServer shaped like the production ones: several config
// sources, one of them listed twice with different prefixes.
func newMCPServer(ns, name string) *agentsv1alpha1.MCPServer {
	return &agentsv1alpha1.MCPServer{
		ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: name},
		Spec: agentsv1alpha1.MCPServerSpec{
			Image:    "ghcr.io/latticeai/mcp-k8s-tools:1.4.0",
			Port:     8080,
			Replicas: ptr.To[int32](2),
			EnvFrom: []corev1.EnvFromSource{
				{SecretRef: &corev1.SecretEnvSource{LocalObjectReference: corev1.LocalObjectReference{Name: "github-app"}}},
				{Prefix: "GH_", SecretRef: &corev1.SecretEnvSource{LocalObjectReference: corev1.LocalObjectReference{Name: "github-app"}}},
				{ConfigMapRef: &corev1.ConfigMapEnvSource{LocalObjectReference: corev1.LocalObjectReference{Name: "tools-config"}}},
				{SecretRef: &corev1.SecretEnvSource{LocalObjectReference: corev1.LocalObjectReference{Name: "otel-token"}}},
				{SecretRef: &corev1.SecretEnvSource{LocalObjectReference: corev1.LocalObjectReference{Name: "vector-db"}}},
			},
		},
	}
}

// setAvailable simulates the Deployment controller, which envtest does not run.
func setAvailable(g Gomega, ns, name string, n int32) {
	d := getDeployment(g, ns, name)
	d.Status.Replicas = n
	d.Status.ReadyReplicas = n
	d.Status.AvailableReplicas = n
	d.Status.UpdatedReplicas = n
	d.Status.ObservedGeneration = d.Generation
	g.Expect(k8sClient.Status().Update(context.Background(), d)).To(Succeed())
}

func getMCP(g Gomega, ns, name string) *agentsv1alpha1.MCPServer {
	var m agentsv1alpha1.MCPServer
	g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: name}, &m)).To(Succeed())
	return &m
}

// reconcileTotal reads controller_runtime_reconcile_total{controller="mcpserver"} (all
// results) from the controller-runtime metrics registry, the same series the
// production dashboard plots.
func reconcileTotal(t *testing.T) float64 {
	t.Helper()
	families, err := crmetrics.Registry.Gather()
	if err != nil {
		t.Fatalf("gather metrics: %v", err)
	}
	var sum float64
	for _, f := range families {
		if f.GetName() != "controller_runtime_reconcile_total" {
			continue
		}
		for _, m := range f.GetMetric() {
			for _, l := range m.GetLabel() {
				if l.GetName() == "controller" && l.GetValue() == "mcpserver" {
					sum += m.GetCounter().GetValue()
				}
			}
		}
	}
	return sum
}

// getDeployment fetches the owned Deployment (same name as the MCPServer).
func getDeployment(g Gomega, ns, name string) *appsv1.Deployment {
	var d appsv1.Deployment
	g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: name}, &d)).To(Succeed())
	return &d
}
