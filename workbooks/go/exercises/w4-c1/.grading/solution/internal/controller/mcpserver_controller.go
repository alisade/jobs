package controller

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/events"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

// MCPServerReconciler reconciles an MCPServer object.
type MCPServerReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder events.EventRecorder
	// CatalogNamespace is where the mcp-catalog ConfigMap lives.
	CatalogNamespace string
}

// +kubebuilder:rbac:groups=agents.example.dev,resources=mcpservers,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=agents.example.dev,resources=mcpservers/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=agents.example.dev,resources=mcpservers/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=configmaps,verbs=get;list;watch;create;update;patch
// +kubebuilder:rbac:groups=events.k8s.io,resources=events,verbs=create;patch

// Reconcile drives one MCPServer toward its desired state.
func (r *MCPServerReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	var mcp agentsv1alpha1.MCPServer
	if err := r.Get(ctx, req.NamespacedName, &mcp); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// Deletion: clean up what Kubernetes GC cannot see, then release the finalizer.
	if !mcp.DeletionTimestamp.IsZero() {
		if controllerutil.ContainsFinalizer(&mcp, FinalizerName) {
			if err := r.deregister(ctx, &mcp); err != nil {
				return ctrl.Result{}, fmt.Errorf("deregister from catalog: %w", err)
			}
			r.event(&mcp, corev1.EventTypeNormal, "Deregistered", "Removed from %s", CatalogConfigMapName)
			controllerutil.RemoveFinalizer(&mcp, FinalizerName)
			if err := r.Update(ctx, &mcp); err != nil {
				return ctrl.Result{}, client.IgnoreNotFound(err)
			}
		}
		return ctrl.Result{}, nil
	}

	if controllerutil.AddFinalizer(&mcp, FinalizerName) {
		if err := r.Update(ctx, &mcp); err != nil {
			return ctrl.Result{}, err // conflict -> requeue with backoff
		}
	}

	// Owned Deployment.
	dep := &appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: mcp.Name, Namespace: mcp.Namespace}}
	depOp, err := controllerutil.CreateOrUpdate(ctx, r.Client, dep, func() error {
		mutateDeployment(dep, &mcp)
		return controllerutil.SetControllerReference(&mcp, dep, r.Scheme)
	})
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconcile deployment: %w", err)
	}

	// Owned Service.
	svc := &corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: mcp.Name, Namespace: mcp.Namespace}}
	svcOp, err := controllerutil.CreateOrUpdate(ctx, r.Client, svc, func() error {
		mutateService(svc, &mcp)
		return controllerutil.SetControllerReference(&mcp, svc, r.Scheme)
	})
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconcile service: %w", err)
	}
	if depOp != controllerutil.OperationResultNone || svcOp != controllerutil.OperationResultNone {
		log.Info("children reconciled", "deployment", depOp, "service", svcOp)
	}

	endpoint := Endpoint(&mcp)
	registered, err := r.register(ctx, &mcp, endpoint)
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("register in catalog: %w", err)
	}
	if registered {
		r.event(&mcp, corev1.EventTypeNormal, "Registered", "Registered %s in %s", endpoint, CatalogConfigMapName)
	}

	// Status from observed children.
	before := mcp.Status.DeepCopy()
	desired := ptr.Deref(mcp.Spec.Replicas, 1)
	available := dep.Status.AvailableReplicas
	mcp.Status.ObservedGeneration = mcp.Generation
	mcp.Status.Endpoint = endpoint
	mcp.Status.AvailableReplicas = available
	setConditions(&mcp, desired, available)

	if !statusEqual(before, &mcp.Status) {
		wasReady := meta.IsStatusConditionTrue(before.Conditions, agentsv1alpha1.ConditionReady)
		if err := r.Status().Update(ctx, &mcp); err != nil {
			return ctrl.Result{}, err
		}
		if nowReady := meta.IsStatusConditionTrue(mcp.Status.Conditions, agentsv1alpha1.ConditionReady); nowReady != wasReady {
			if nowReady {
				r.event(&mcp, corev1.EventTypeNormal, "Ready", "%d/%d replicas available", available, desired)
			} else {
				r.event(&mcp, corev1.EventTypeWarning, "NotReady", "%d/%d replicas available", available, desired)
			}
		}
	}
	return ctrl.Result{}, nil
}

func (r *MCPServerReconciler) event(obj runtime.Object, typ, reason, note string, args ...any) {
	if r.Recorder != nil {
		r.Recorder.Eventf(obj, nil, typ, reason, "Reconcile", note, args...)
	}
}

func setConditions(mcp *agentsv1alpha1.MCPServer, desired, available int32) {
	gen := mcp.Generation
	set := func(t string, s metav1.ConditionStatus, reason, msg string) {
		meta.SetStatusCondition(&mcp.Status.Conditions, metav1.Condition{
			Type: t, Status: s, Reason: reason, Message: msg, ObservedGeneration: gen,
		})
	}
	msg := fmt.Sprintf("%d/%d replicas available", available, desired)
	switch {
	case available >= desired:
		set(agentsv1alpha1.ConditionReady, metav1.ConditionTrue, "MinimumReplicasAvailable", msg)
		set(agentsv1alpha1.ConditionProgressing, metav1.ConditionFalse, "RolloutComplete", msg)
		set(agentsv1alpha1.ConditionDegraded, metav1.ConditionFalse, "AsExpected", msg)
	case available == 0:
		set(agentsv1alpha1.ConditionReady, metav1.ConditionFalse, "ReplicasUnavailable", msg)
		set(agentsv1alpha1.ConditionProgressing, metav1.ConditionTrue, "RollingOut", msg)
		set(agentsv1alpha1.ConditionDegraded, metav1.ConditionTrue, "NoReplicasAvailable", msg)
	default:
		set(agentsv1alpha1.ConditionReady, metav1.ConditionFalse, "ReplicasUnavailable", msg)
		set(agentsv1alpha1.ConditionProgressing, metav1.ConditionTrue, "RollingOut", msg)
		set(agentsv1alpha1.ConditionDegraded, metav1.ConditionFalse, "AsExpected", msg)
	}
}

// statusEqual ignores LastTransitionTime churn: SetStatusCondition only bumps it on a
// status flip, so comparing the full structs is enough here.
func statusEqual(a, b *agentsv1alpha1.MCPServerStatus) bool {
	if a.ObservedGeneration != b.ObservedGeneration || a.Endpoint != b.Endpoint ||
		a.AvailableReplicas != b.AvailableReplicas || len(a.Conditions) != len(b.Conditions) {
		return false
	}
	for _, c := range a.Conditions {
		o := meta.FindStatusCondition(b.Conditions, c.Type)
		if o == nil || o.Status != c.Status || o.Reason != c.Reason || o.Message != c.Message ||
			o.ObservedGeneration != c.ObservedGeneration {
			return false
		}
	}
	return true
}

func mutateDeployment(dep *appsv1.Deployment, mcp *agentsv1alpha1.MCPServer) {
	labels := Labels(mcp)
	if dep.Labels == nil {
		dep.Labels = map[string]string{}
	}
	for k, v := range labels {
		dep.Labels[k] = v
	}
	dep.Spec.Replicas = ptr.To(ptr.Deref(mcp.Spec.Replicas, 1))
	// Selector is immutable: only set it on create.
	if dep.Spec.Selector == nil {
		dep.Spec.Selector = &metav1.LabelSelector{MatchLabels: labels}
	}
	dep.Spec.Template.Labels = labels
	port := portOf(mcp)
	c := corev1.Container{
		Name:  ContainerName,
		Image: mcp.Spec.Image,
		Ports: []corev1.ContainerPort{{Name: PortName, ContainerPort: port, Protocol: corev1.ProtocolTCP}},
		Env: []corev1.EnvVar{
			{Name: "MCP_TRANSPORT", Value: string(transportOf(mcp))},
			{Name: "MCP_PATH", Value: pathOf(mcp)},
			{Name: "MCP_PORT", Value: fmt.Sprint(port)},
		},
		EnvFrom: mcp.Spec.EnvFrom,
	}
	// Replace the container we own; keep anything else (e.g. injected sidecars) intact.
	containers := dep.Spec.Template.Spec.Containers
	replaced := false
	for i := range containers {
		if containers[i].Name == ContainerName {
			// Preserve API-server defaulted fields we do not manage.
			c.TerminationMessagePath = containers[i].TerminationMessagePath
			c.TerminationMessagePolicy = containers[i].TerminationMessagePolicy
			c.ImagePullPolicy = containers[i].ImagePullPolicy
			containers[i] = c
			replaced = true
		}
	}
	if !replaced {
		containers = append(containers, c)
	}
	dep.Spec.Template.Spec.Containers = containers
}

func mutateService(svc *corev1.Service, mcp *agentsv1alpha1.MCPServer) {
	labels := Labels(mcp)
	if svc.Labels == nil {
		svc.Labels = map[string]string{}
	}
	for k, v := range labels {
		svc.Labels[k] = v
	}
	svc.Spec.Selector = labels
	svc.Spec.Ports = []corev1.ServicePort{{
		Name:       PortName,
		Port:       portOf(mcp),
		TargetPort: intstr.FromString(PortName),
		Protocol:   corev1.ProtocolTCP,
	}}
}

// register upserts this server's entry in the catalog ConfigMap. It reports whether it
// changed anything.
func (r *MCPServerReconciler) register(ctx context.Context, mcp *agentsv1alpha1.MCPServer, endpoint string) (bool, error) {
	key := CatalogKey(mcp)
	var cm corev1.ConfigMap
	err := r.Get(ctx, types.NamespacedName{Namespace: r.CatalogNamespace, Name: CatalogConfigMapName}, &cm)
	if apierrors.IsNotFound(err) {
		cm = corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{Namespace: r.CatalogNamespace, Name: CatalogConfigMapName},
			Data:       map[string]string{key: endpoint},
		}
		return true, r.Create(ctx, &cm)
	}
	if err != nil {
		return false, err
	}
	if cm.Data[key] == endpoint {
		return false, nil
	}
	if cm.Data == nil {
		cm.Data = map[string]string{}
	}
	cm.Data[key] = endpoint
	return true, r.Update(ctx, &cm) // optimistic concurrency: conflict -> requeue
}

func (r *MCPServerReconciler) deregister(ctx context.Context, mcp *agentsv1alpha1.MCPServer) error {
	var cm corev1.ConfigMap
	err := r.Get(ctx, types.NamespacedName{Namespace: r.CatalogNamespace, Name: CatalogConfigMapName}, &cm)
	if apierrors.IsNotFound(err) {
		return nil // nothing to clean up; never block deletion on a missing catalog
	}
	if err != nil {
		return err
	}
	if _, ok := cm.Data[CatalogKey(mcp)]; !ok {
		return nil
	}
	delete(cm.Data, CatalogKey(mcp))
	return r.Update(ctx, &cm)
}

// SetupWithManager registers the controller: watch MCPServers and the children it owns.
func (r *MCPServerReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&agentsv1alpha1.MCPServer{}).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		Named("mcpserver").
		Complete(r)
}
