// Package reloader rolls Deployments when an opted-in ConfigMap changes.
// See README.md for the contract.
package reloader

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"maps"
	"slices"
	"strings"
	"sync"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/types"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	appslisters "k8s.io/client-go/listers/apps/v1"
	corelisters "k8s.io/client-go/listers/core/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/workqueue"
)

const (
	// WatchLabel opts a ConfigMap in (value must be "true").
	WatchLabel = "reloader.lumenpay.io/watch"
	// ReferenceAnnotation on a Deployment lists ConfigMap names (comma separated)
	// in the same namespace that should roll it.
	ReferenceAnnotation = "reloader.lumenpay.io/configmaps"
	// HashAnnotationPrefix + <configmap name> is the pod template annotation key
	// that carries the ConfigMap content hash.
	HashAnnotationPrefix = "cm.reloader.lumenpay.io/"
)

// ErrCacheSync is returned by Run when the informer caches never sync.
var ErrCacheSync = errors.New("reloader: timed out waiting for caches to sync")

// Options tunes the controller. The zero value is production-ready.
type Options struct {
	// RateLimiter for failed items; nil means workqueue.DefaultTypedControllerRateLimiter.
	RateLimiter workqueue.TypedRateLimiter[string]
	// MaxRetries is how many times a failing key is requeued before it is dropped; 0 means 5.
	MaxRetries int
	// Logger; nil means slog.Default().
	Logger *slog.Logger
}

// Controller watches ConfigMaps and patches referencing Deployments.
type Controller struct {
	client       kubernetes.Interface
	cmLister     corelisters.ConfigMapLister
	deployLister appslisters.DeploymentLister
	synced       []cache.InformerSynced
	queue        workqueue.TypedRateLimitingInterface[string]
	maxRetries   int
	log          *slog.Logger
}

// NewController wires event handlers onto the factory's ConfigMap and Deployment
// informers. The caller starts the factory; Run waits for the caches.
func NewController(client kubernetes.Interface, factory informers.SharedInformerFactory, opts Options) (*Controller, error) {
	if client == nil || factory == nil {
		return nil, errors.New("reloader: client and factory are required")
	}
	rl := opts.RateLimiter
	if rl == nil {
		rl = workqueue.DefaultTypedControllerRateLimiter[string]()
	}
	c := &Controller{
		client:     client,
		maxRetries: opts.MaxRetries,
		log:        opts.Logger,
		queue: workqueue.NewTypedRateLimitingQueueWithConfig(rl,
			workqueue.TypedRateLimitingQueueConfig[string]{Name: "config-reloader"}),
	}
	if c.maxRetries <= 0 {
		c.maxRetries = 5
	}
	if c.log == nil {
		c.log = slog.Default()
	}

	cmInformer := factory.Core().V1().ConfigMaps()
	deployInformer := factory.Apps().V1().Deployments()
	c.cmLister = cmInformer.Lister()
	c.deployLister = deployInformer.Lister()
	c.synced = []cache.InformerSynced{cmInformer.Informer().HasSynced, deployInformer.Informer().HasSynced}

	if _, err := cmInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc:    c.onConfigMapAdd,
		UpdateFunc: c.onConfigMapUpdate,
		DeleteFunc: c.onConfigMapDelete,
	}); err != nil {
		return nil, fmt.Errorf("reloader: configmap handler: %w", err)
	}
	if _, err := deployInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc:    c.onDeploymentChange,
		UpdateFunc: func(_, newObj any) { c.onDeploymentChange(newObj) },
	}); err != nil {
		return nil, fmt.Errorf("reloader: deployment handler: %w", err)
	}
	return c, nil
}

// Run waits for caches, starts workers and blocks until ctx is done.
func (c *Controller) Run(ctx context.Context, workers int) error {
	defer utilruntime.HandleCrash()
	defer c.queue.ShutDown()
	if workers < 1 {
		workers = 1
	}
	c.log.Info("starting config-reloader", "workers", workers)
	if !cache.WaitForNamedCacheSyncWithContext(ctx, c.synced...) {
		return ErrCacheSync
	}
	var wg sync.WaitGroup
	for range workers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			wait.UntilWithContext(ctx, c.runWorker, time.Second)
		}()
	}
	<-ctx.Done()
	c.log.Info("shutting down config-reloader")
	c.queue.ShutDown()
	wg.Wait()
	return nil
}

func (c *Controller) runWorker(ctx context.Context) {
	for c.processNextItem(ctx) {
	}
}

func (c *Controller) processNextItem(ctx context.Context) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	err := c.reconcile(ctx, key)
	switch {
	case err == nil:
		c.queue.Forget(key)
	case c.queue.NumRequeues(key) < c.maxRetries:
		c.log.Warn("reconcile failed, requeueing", "key", key, "err", err,
			"requeues", c.queue.NumRequeues(key))
		c.queue.AddRateLimited(key)
	default:
		c.log.Error("reconcile failed, dropping key", "key", key, "err", err)
		c.queue.Forget(key)
		utilruntime.HandleError(err)
	}
	return true
}

// reconcile brings every Deployment that references the ConfigMap at key to the
// ConfigMap's current hash (or removes the hash when the ConfigMap is gone).
func (c *Controller) reconcile(ctx context.Context, key string) error {
	ns, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		return nil // malformed key: retrying will not help
	}
	hash := ""
	cm, err := c.cmLister.ConfigMaps(ns).Get(name)
	switch {
	case apierrors.IsNotFound(err):
		// deleted: hash stays "" and the annotation is removed
	case err != nil:
		return err
	case !watched(cm):
		return nil // label removed: stop managing, leave Deployments alone
	default:
		hash = HashConfigMap(cm)
	}

	deps, err := c.deployLister.Deployments(ns).List(labels.Everything())
	if err != nil {
		return err
	}
	var errs []error
	annKey := HashAnnotationPrefix + name
	for _, d := range deps {
		if !slices.Contains(ReferencedConfigMaps(d), name) {
			continue
		}
		current, has := d.Spec.Template.Annotations[annKey]
		if (hash == "" && !has) || (hash != "" && current == hash) {
			continue // already converged: no write
		}
		if err := c.patchDeployment(ctx, d, annKey, hash); err != nil {
			errs = append(errs, fmt.Errorf("patch %s/%s: %w", d.Namespace, d.Name, err))
			continue
		}
		c.log.Info("rolled deployment", "deployment", d.Namespace+"/"+d.Name, "configmap", name, "hash", hash)
	}
	return errors.Join(errs...)
}

func (c *Controller) patchDeployment(ctx context.Context, d *appsv1.Deployment, annKey, hash string) error {
	var val any = hash
	if hash == "" {
		val = nil // JSON merge patch: null deletes the key
	}
	patch := map[string]any{
		"spec": map[string]any{
			"template": map[string]any{
				"metadata": map[string]any{
					"annotations": map[string]any{annKey: val},
				},
			},
		},
	}
	body, err := json.Marshal(patch)
	if err != nil {
		return err
	}
	_, err = c.client.AppsV1().Deployments(d.Namespace).Patch(ctx, d.Name, types.MergePatchType, body, metav1.PatchOptions{})
	return err
}

func (c *Controller) onConfigMapAdd(obj any) {
	if cm, ok := obj.(*corev1.ConfigMap); ok && watched(cm) {
		c.enqueue(cm)
	}
}

func (c *Controller) onConfigMapUpdate(oldObj, newObj any) {
	oldCM, ok1 := oldObj.(*corev1.ConfigMap)
	newCM, ok2 := newObj.(*corev1.ConfigMap)
	if !ok1 || !ok2 || !watched(newCM) {
		return
	}
	if oldCM.ResourceVersion == newCM.ResourceVersion && watched(oldCM) {
		return // periodic resync, nothing changed
	}
	c.enqueue(newCM)
}

func (c *Controller) onConfigMapDelete(obj any) {
	if tomb, ok := obj.(cache.DeletedFinalStateUnknown); ok {
		obj = tomb.Obj
	}
	cm, ok := obj.(*corev1.ConfigMap)
	if !ok || !watched(cm) {
		return
	}
	c.enqueue(cm)
}

func (c *Controller) onDeploymentChange(obj any) {
	d, ok := obj.(*appsv1.Deployment)
	if !ok {
		return
	}
	for _, name := range ReferencedConfigMaps(d) {
		c.queue.Add(d.Namespace + "/" + name)
	}
}

func (c *Controller) enqueue(cm *corev1.ConfigMap) {
	key, err := cache.MetaNamespaceKeyFunc(cm)
	if err != nil {
		utilruntime.HandleError(err)
		return
	}
	c.queue.Add(key)
}

func watched(cm *corev1.ConfigMap) bool { return cm.Labels[WatchLabel] == "true" }

// ReferencedConfigMaps parses the Deployment's ReferenceAnnotation.
func ReferencedConfigMaps(d *appsv1.Deployment) []string {
	raw := d.Annotations[ReferenceAnnotation]
	var out []string
	for _, part := range strings.Split(raw, ",") {
		if p := strings.TrimSpace(part); p != "" {
			out = append(out, p)
		}
	}
	return out
}

// HashConfigMap returns the lowercase hex SHA-256 of the ConfigMap content:
// Data and BinaryData, keys in sorted order, unambiguously delimited. It is
// independent of map iteration order and of metadata.
func HashConfigMap(cm *corev1.ConfigMap) string {
	h := sha256.New()
	write := func(section string, keys []string, val func(string) []byte) {
		for _, k := range keys {
			fmt.Fprintf(h, "%s:%d:%s:", section, len(k), k)
			v := val(k)
			fmt.Fprintf(h, "%d:", len(v))
			h.Write(v)
		}
	}
	dataKeys := slices.Sorted(maps.Keys(cm.Data))
	write("d", dataKeys, func(k string) []byte { return []byte(cm.Data[k]) })
	binKeys := slices.Sorted(maps.Keys(cm.BinaryData))
	write("b", binKeys, func(k string) []byte { return cm.BinaryData[k] })
	return hex.EncodeToString(h.Sum(nil))
}
