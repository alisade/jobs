package controller

import (
	"cmp"
	"fmt"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

// Names and conventions shared by the reconciler and the tests. Do not change them.
const (
	// FinalizerName guards catalog cleanup.
	FinalizerName = "agents.example.dev/catalog"
	// CatalogConfigMapName is the ConfigMap-backed registry the platform gateway reads.
	CatalogConfigMapName = "mcp-catalog"
	// ContainerName is the name of the MCP server container in the Deployment.
	ContainerName = "mcp-server"
	// PortName names the container port and the Service port.
	PortName = "mcp"
)

// Labels are set on the Deployment, its pod template, and the Service; they are also
// the Deployment selector and the Service selector.
func Labels(mcp *agentsv1alpha1.MCPServer) map[string]string {
	return map[string]string{
		"app.kubernetes.io/name":       "mcp-server",
		"app.kubernetes.io/instance":   mcp.Name,
		"app.kubernetes.io/managed-by": "agent-fleet-operator",
	}
}

// CatalogKey is the key of this server in the mcp-catalog ConfigMap data.
func CatalogKey(mcp *agentsv1alpha1.MCPServer) string {
	return mcp.Namespace + "." + mcp.Name
}

// Endpoint is the in-cluster URL for the server, also written to status.endpoint and
// to the catalog: http://<name>.<namespace>.svc.cluster.local:<port><path>
func Endpoint(mcp *agentsv1alpha1.MCPServer) string {
	return fmt.Sprintf("http://%s.%s.svc.cluster.local:%d%s", mcp.Name, mcp.Namespace, portOf(mcp), pathOf(mcp))
}

// The CRD defaults these fields, but a reconciler must not assume defaulting ran
// (older objects, tests with a bare client).
func portOf(mcp *agentsv1alpha1.MCPServer) int32 { return cmp.Or(mcp.Spec.Port, 8080) }
func pathOf(mcp *agentsv1alpha1.MCPServer) string { return cmp.Or(mcp.Spec.Path, "/mcp") }
func transportOf(mcp *agentsv1alpha1.MCPServer) agentsv1alpha1.Transport {
	return cmp.Or(mcp.Spec.Transport, agentsv1alpha1.TransportStreamableHTTP)
}
