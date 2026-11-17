package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// Transport is how MCP clients talk to the server.
// +kubebuilder:validation:Enum=streamable-http;sse
type Transport string

const (
	TransportStreamableHTTP Transport = "streamable-http"
	TransportSSE            Transport = "sse"
)

// Condition types written to MCPServer status.conditions.
const (
	ConditionReady       = "Ready"
	ConditionProgressing = "Progressing"
	ConditionDegraded    = "Degraded"
)

// MCPServerSpec is the desired state of an MCP server.
// +kubebuilder:validation:XValidation:rule="self.transport != 'sse' || self.port != 443",message="sse transport cannot use port 443 in this platform"
type MCPServerSpec struct {
	// Image is the container image that serves MCP.
	// +kubebuilder:validation:MinLength=1
	Image string `json:"image"`

	// Port the container listens on; the Service exposes the same port.
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=65535
	// +kubebuilder:default=8080
	// +optional
	Port int32 `json:"port,omitempty"`

	// Replicas of the server Deployment.
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:default=1
	// +optional
	Replicas *int32 `json:"replicas,omitempty"`

	// Transport exposed by the server.
	// +kubebuilder:default=streamable-http
	// +optional
	Transport Transport `json:"transport,omitempty"`

	// Path the MCP endpoint is served on.
	// +kubebuilder:default=/mcp
	// +optional
	Path string `json:"path,omitempty"`

	// EnvFrom injects environment variables from Secrets or ConfigMaps (API keys, config).
	// +optional
	EnvFrom []corev1.EnvFromSource `json:"envFrom,omitempty"`
}

// MCPServerStatus is the observed state of an MCP server.
type MCPServerStatus struct {
	// ObservedGeneration is the .metadata.generation the status was computed for.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Endpoint is the in-cluster URL clients use, e.g. http://name.ns.svc.cluster.local:8080/mcp.
	// +optional
	Endpoint string `json:"endpoint,omitempty"`

	// AvailableReplicas mirrors the Deployment.
	// +optional
	AvailableReplicas int32 `json:"availableReplicas,omitempty"`

	// LastReconcileID is the controller-runtime reconcileID of the reconcile that
	// produced this status, so support can find the matching log lines (PLAT-2291).
	// +optional
	LastReconcileID string `json:"lastReconcileID,omitempty"`

	// Conditions: Ready, Progressing, Degraded.
	// +listType=map
	// +listMapKey=type
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// MCPServer runs one Model Context Protocol server as a Deployment + Service.
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:shortName=mcps
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=`.status.conditions[?(@.type=="Ready")].status`
// +kubebuilder:printcolumn:name="Endpoint",type=string,JSONPath=`.status.endpoint`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`
type MCPServer struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MCPServerSpec   `json:"spec,omitempty"`
	Status MCPServerStatus `json:"status,omitempty"`
}

// MCPServerList contains a list of MCPServer.
// +kubebuilder:object:root=true
type MCPServerList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []MCPServer `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MCPServer{}, &MCPServerList{})
}
