package controller

import (
	"context"

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/events"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
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
// TODO: RBAC markers for everything else the controller reads or writes.

// Reconcile drives one MCPServer toward its desired state. See README.md "Requirements".
func (r *MCPServerReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	var mcp agentsv1alpha1.MCPServer
	if err := r.Get(ctx, req.NamespacedName, &mcp); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}
	log.V(1).Info("reconciling", "generation", mcp.Generation)

	// TODO 1: deletion - if DeletionTimestamp is set and FinalizerName is present,
	//         deregister from the catalog, then remove the finalizer.
	// TODO 2: add FinalizerName if missing.
	// TODO 3: Deployment + Service via controllerutil.CreateOrUpdate with a controller
	//         owner reference (see naming.go for names, labels and ports).
	// TODO 4: register Endpoint(mcp) under CatalogKey(mcp) in the mcp-catalog ConfigMap
	//         in r.CatalogNamespace (create it if it does not exist).
	// TODO 5: status: observedGeneration, endpoint, availableReplicas, and the Ready /
	//         Progressing / Degraded conditions via meta.SetStatusCondition.
	// TODO 6: Events for meaningful transitions (r.Recorder may be nil in unit tests).
	return ctrl.Result{}, nil
}

// SetupWithManager registers the controller with the manager.
func (r *MCPServerReconciler) SetupWithManager(mgr ctrl.Manager) error {
	// TODO: watch the children this controller owns, so drift triggers a reconcile.
	return ctrl.NewControllerManagedBy(mgr).
		For(&agentsv1alpha1.MCPServer{}).
		Named("mcpserver").
		Complete(r)
}
