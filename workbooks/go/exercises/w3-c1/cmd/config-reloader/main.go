// Command config-reloader rolls Deployments when opted-in ConfigMaps change.
package main

import (
	"context"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/lumenpay/config-reloader/reloader"
)

func main() {
	kubeconfig := flag.String("kubeconfig", "", "path to kubeconfig (empty = in-cluster)")
	workers := flag.Int("workers", 2, "concurrent reconcile workers")
	flag.Parse()
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	var cfg *rest.Config
	var err error
	if *kubeconfig != "" {
		cfg, err = clientcmd.BuildConfigFromFlags("", *kubeconfig)
	} else {
		cfg, err = rest.InClusterConfig()
	}
	if err != nil {
		log.Error("kube config", "err", err)
		os.Exit(2)
	}
	client, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		log.Error("client", "err", err)
		os.Exit(2)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	factory := informers.NewSharedInformerFactory(client, 0)
	ctrl, err := reloader.NewController(client, factory, reloader.Options{Logger: log})
	if err != nil {
		log.Error("controller", "err", err)
		os.Exit(2)
	}
	factory.Start(ctx.Done())
	defer factory.Shutdown()
	if err := ctrl.Run(ctx, *workers); err != nil {
		log.Error("run", "err", err)
		os.Exit(1)
	}
}
