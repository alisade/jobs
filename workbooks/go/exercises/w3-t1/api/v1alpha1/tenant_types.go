package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TenantSpec defines the desired state of Tenant.
type TenantSpec struct {
	// CPU is the total CPU request quota for the tenant namespace, e.g. "8".
	// +kubebuilder:validation:Required
	CPU string `json:"cpu"`
	// Memory is the total memory request quota, e.g. "32Gi".
	// +kubebuilder:validation:Required
	Memory string `json:"memory"`
	// BucketPrefix is the S3 prefix the tenant's workloads may use.
	// +kubebuilder:validation:Pattern=`^[a-z0-9-]+/$`
	BucketPrefix string `json:"bucketPrefix"`
}

// TenantStatus defines the observed state of Tenant.
type TenantStatus struct {
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`
	// +optional
	// +listType=map
	// +listMapKey=type
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=`.status.conditions[?(@.type=="Ready")].status`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// Tenant is a team's slice of the shared analytics cluster: a ResourceQuota and
// a Secret describing its storage prefix, both owned by the Tenant.
type Tenant struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   TenantSpec   `json:"spec,omitempty"`
	Status TenantStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// TenantList contains a list of Tenant.
type TenantList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Tenant `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Tenant{}, &TenantList{})
}
