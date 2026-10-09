package controller

import (
	"context"
	"fmt"
	"reflect"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

// MCPServerReconciler reconciles an MCPServer object.
//
// agent-fleet-operator v0.3.1. Changes since v0.2.4 (CHANGELOG excerpt):
//   - feat: status.lastReconcileID so support can correlate status with logs (PLAT-2291)
//   - chore: client QPS/Burst raised 20/30 -> 100/200 after throttling alerts (INC-4412)
//   - chore: bump controller-runtime
type MCPServerReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=agents.example.dev,resources=mcpservers,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=agents.example.dev,resources=mcpservers/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete

// Reconcile drives one MCPServer toward its desired state.
func (r *MCPServerReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	var mcp agentsv1alpha1.MCPServer
	if err := r.Get(ctx, req.NamespacedName, &mcp); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	dep := &appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: mcp.Name, Namespace: mcp.Namespace}}
	depOp, err := controllerutil.CreateOrUpdate(ctx, r.Client, dep, func() error {
		mutateDeployment(dep, &mcp)
		return controllerutil.SetControllerReference(&mcp, dep, r.Scheme)
	})
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconcile deployment: %w", err)
	}

	svc := &corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: mcp.Name, Namespace: mcp.Namespace}}
	svcOp, err := controllerutil.CreateOrUpdate(ctx, r.Client, svc, func() error {
		mutateService(svc, &mcp)
		return controllerutil.SetControllerReference(&mcp, svc, r.Scheme)
	})
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconcile service: %w", err)
	}

	// Status. Only write when something changed, so we do not hammer the API server.
	before := mcp.Status.DeepCopy()
	desired := ptr.Deref(mcp.Spec.Replicas, 1)
	available := dep.Status.AvailableReplicas
	mcp.Status.ObservedGeneration = mcp.Generation
	mcp.Status.Endpoint = Endpoint(&mcp)
	mcp.Status.AvailableReplicas = available
	// Status must be a pure function of observed state. The reconcileID changes on
	// every run, so writing it made every reconcile a status write, and every status
	// write a watch event that enqueued the next reconcile. The ID is already on every
	// log line (controller-runtime adds it to the logger), which is what PLAT-2291
	// actually needed. The field is deprecated and no longer written.
	setConditions(&mcp, desired, available)

	if !reflect.DeepEqual(before, &mcp.Status) {
		if err := r.Status().Update(ctx, &mcp); err != nil {
			return ctrl.Result{}, err
		}
		log.V(1).Info("status updated", "available", available, "desired", desired)
	}
	if depOp != controllerutil.OperationResultNone || svcOp != controllerutil.OperationResultNone {
		log.Info("children reconciled", "deployment", depOp, "service", svcOp)
	}
	return ctrl.Result{}, nil
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

func mutateDeployment(dep *appsv1.Deployment, mcp *agentsv1alpha1.MCPServer) {
	labels := Labels(mcp)
	if dep.Labels == nil {
		dep.Labels = map[string]string{}
	}
	for k, v := range labels {
		dep.Labels[k] = v
	}
	dep.Spec.Replicas = ptr.To(ptr.Deref(mcp.Spec.Replicas, 1))
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
	containers := dep.Spec.Template.Spec.Containers
	replaced := false
	for i := range containers {
		if containers[i].Name == ContainerName {
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

// SetupWithManager registers the controller: MCPServers and the children it owns.
//
// Defense in depth: on the primary resource only, ignore updates that do not change
// metadata.generation (status-only and most metadata-only writes), but still react to
// label/annotation changes. Do NOT apply it globally with WithEventFilter: Deployment
// status changes (availableReplicas) do not bump generation, and Ready depends on them.
func (r *MCPServerReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&agentsv1alpha1.MCPServer{}, builder.WithPredicates(predicate.Or(
			predicate.GenerationChangedPredicate{},
			predicate.LabelChangedPredicate{},
			predicate.AnnotationChangedPredicate{},
		))).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		Named("mcpserver").
		Complete(r)
}
