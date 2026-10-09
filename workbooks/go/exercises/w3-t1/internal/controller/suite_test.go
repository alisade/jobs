package controller

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"

	platformv1alpha1 "github.com/harbor-analytics/tenant-operator/api/v1alpha1"
)

// Shared envtest control plane (kube-apiserver + etcd, RBAC authorization on).
var (
	testEnv     *envtest.Environment
	adminCfg    *rest.Config
	adminClient client.Client
	testScheme  = runtime.NewScheme()
)

func TestMain(m *testing.M) {
	logf.SetLogger(zap.New(zap.WriteTo(os.Stderr), zap.UseDevMode(true)))
	if os.Getenv("KUBEBUILDER_ASSETS") == "" {
		fmt.Fprintln(os.Stderr, "KUBEBUILDER_ASSETS is not set: run tests with `make test` (it runs setup-envtest)")
		os.Exit(1)
	}
	_ = clientgoscheme.AddToScheme(testScheme)
	_ = platformv1alpha1.AddToScheme(testScheme)

	testEnv = &envtest.Environment{
		CRDDirectoryPaths:     []string{filepath.Join("..", "..", "config", "crd", "bases")},
		ErrorIfCRDPathMissing: true,
	}
	var err error
	adminCfg, err = testEnv.Start()
	if err != nil {
		fmt.Fprintln(os.Stderr, "start envtest:", err)
		os.Exit(1)
	}
	adminClient, err = client.New(adminCfg, client.Options{Scheme: testScheme})
	if err != nil {
		fmt.Fprintln(os.Stderr, "admin client:", err)
		_ = testEnv.Stop()
		os.Exit(1)
	}
	code := m.Run()
	_ = testEnv.Stop()
	os.Exit(code)
}
