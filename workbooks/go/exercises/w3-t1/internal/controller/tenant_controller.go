// Package controller reconciles Tenant objects.
package controller

import (
	"context"
	"fmt"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/events"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	platformv1alpha1 "github.com/harbor-analytics/tenant-operator/api/v1alpha1"
)

// Labels and names of the children the operator owns.
const (
	ManagedByLabel = "app.kubernetes.io/managed-by"
	ManagedByValue = "tenant-operator"
	ConditionReady = "Ready"
)

// TenantReconciler reconciles a Tenant object.
type TenantReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder events.EventRecorder
}

// +kubebuilder:rbac:groups=platform.harbor-analytics.io,resources=tenants,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=platform.harbor-analytics.io,resources=tenants/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=platform.harbor-analytics.io,resources=tenants/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=resourcequotas,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;create;update;patch;delete
// +kubebuilder:rbac:groups=events.k8s.io,resources=events,verbs=create;patch

// Reconcile converges a Tenant's ResourceQuota and storage Secret.
func (r *TenantReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	var tenant platformv1alpha1.Tenant
	if err := r.Get(ctx, req.NamespacedName, &tenant); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	quota := &corev1.ResourceQuota{ObjectMeta: metav1.ObjectMeta{Name: QuotaName(&tenant), Namespace: tenant.Namespace}}
	op, err := controllerutil.CreateOrUpdate(ctx, r.Client, quota, func() error {
		desired, err := DesiredQuota(&tenant)
		if err != nil {
			return err
		}
		quota.Labels = desired.Labels
		quota.Spec = desired.Spec
		return controllerutil.SetControllerReference(&tenant, quota, r.Scheme)
	})
	if err != nil {
		return r.fail(ctx, &tenant, "QuotaFailed", err)
	}
	log.V(1).Info("resourcequota reconciled", "operation", op)

	secret := &corev1.Secret{ObjectMeta: metav1.ObjectMeta{Name: SecretName(&tenant), Namespace: tenant.Namespace}}
	op, err = controllerutil.CreateOrUpdate(ctx, r.Client, secret, func() error {
		desired := DesiredSecret(&tenant)
		secret.Labels = desired.Labels
		secret.Type = desired.Type
		secret.StringData = nil
		secret.Data = desired.Data
		return controllerutil.SetControllerReference(&tenant, secret, r.Scheme)
	})
	if err != nil {
		return r.fail(ctx, &tenant, "SecretFailed", err)
	}
	log.V(1).Info("secret reconciled", "operation", op)

	changed := meta.SetStatusCondition(&tenant.Status.Conditions, metav1.Condition{
		Type: ConditionReady, Status: metav1.ConditionTrue, Reason: "Reconciled",
		Message: "quota and storage secret are in place", ObservedGeneration: tenant.Generation,
	})
	if changed || tenant.Status.ObservedGeneration != tenant.Generation {
		tenant.Status.ObservedGeneration = tenant.Generation
		if err := r.Status().Update(ctx, &tenant); err != nil {
			if apierrors.IsConflict(err) {
				return ctrl.Result{Requeue: true}, nil
			}
			return ctrl.Result{}, err
		}
		if r.Recorder != nil {
			r.Recorder.Eventf(&tenant, nil, corev1.EventTypeNormal, "Reconciled", "Reconcile", "tenant %s is ready", tenant.Name)
		}
	}
	return ctrl.Result{}, nil
}

func (r *TenantReconciler) fail(ctx context.Context, t *platformv1alpha1.Tenant, reason string, cause error) (ctrl.Result, error) {
	meta.SetStatusCondition(&t.Status.Conditions, metav1.Condition{
		Type: ConditionReady, Status: metav1.ConditionFalse, Reason: reason,
		Message: cause.Error(), ObservedGeneration: t.Generation,
	})
	if err := r.Status().Update(ctx, t); err != nil && !apierrors.IsConflict(err) {
		logf.FromContext(ctx).Error(err, "status update failed")
	}
	return ctrl.Result{}, cause
}

// SetupWithManager registers the controller. v0.4.0 added Owns(&corev1.Secret{})
// so a deleted or hand-edited storage Secret is restored immediately (SEC-2291).
func (r *TenantReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&platformv1alpha1.Tenant{}).
		Owns(&corev1.ResourceQuota{}).
		Owns(&corev1.Secret{}).
		Named("tenant").
		Complete(r)
}

// QuotaName is the name of the Tenant's ResourceQuota.
func QuotaName(t *platformv1alpha1.Tenant) string { return "tenant-" + t.Name }

// SecretName is the name of the Tenant's storage Secret.
func SecretName(t *platformv1alpha1.Tenant) string { return "tenant-" + t.Name + "-storage" }

// DesiredQuota builds the ResourceQuota for a Tenant.
func DesiredQuota(t *platformv1alpha1.Tenant) (*corev1.ResourceQuota, error) {
	cpu, err := resource.ParseQuantity(t.Spec.CPU)
	if err != nil {
		return nil, fmt.Errorf("spec.cpu: %w", err)
	}
	mem, err := resource.ParseQuantity(t.Spec.Memory)
	if err != nil {
		return nil, fmt.Errorf("spec.memory: %w", err)
	}
	return &corev1.ResourceQuota{
		ObjectMeta: metav1.ObjectMeta{Name: QuotaName(t), Namespace: t.Namespace,
			Labels: map[string]string{ManagedByLabel: ManagedByValue}},
		Spec: corev1.ResourceQuotaSpec{Hard: corev1.ResourceList{
			corev1.ResourceRequestsCPU:    cpu,
			corev1.ResourceRequestsMemory: mem,
		}},
	}, nil
}

// DesiredSecret builds the storage Secret for a Tenant.
func DesiredSecret(t *platformv1alpha1.Tenant) *corev1.Secret {
	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{Name: SecretName(t), Namespace: t.Namespace,
			Labels: map[string]string{ManagedByLabel: ManagedByValue}},
		Type: corev1.SecretTypeOpaque,
		Data: map[string][]byte{
			"bucket": []byte("harbor-analytics-tenants"),
			"prefix": []byte(t.Spec.BucketPrefix),
		},
	}
}
