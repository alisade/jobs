// Package meshsim is a small, offline model of the parts of Istio that decide
// whether one workload can call another: sidecar injection (driven by the real
// MutatingWebhookConfiguration selectors), peer authentication (mTLS or
// plaintext), and AuthorizationPolicy evaluation (DENY first, then ALLOW).
//
// It reads the manifests in manifests/ and the installed injector webhook in
// artifacts/istio/. It is deliberately simplified: no `when` conditions, no
// CUSTOM action, no ports, no ambient mode, single trust domain cluster.local.
// Do not edit it to make a test pass; fix the manifests.
package meshsim

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	admissionv1 "k8s.io/api/admissionregistration/v1"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"sigs.k8s.io/yaml"
)

// RootNamespace is Istio's root config namespace (mesh-wide policies).
const RootNamespace = "istio-system"

// ---- Istio CRD shapes (only the fields the model uses) ----------------------

type WorkloadSelector struct {
	MatchLabels map[string]string `json:"matchLabels,omitempty"`
}

type Source struct {
	Principals        []string `json:"principals,omitempty"`
	NotPrincipals     []string `json:"notPrincipals,omitempty"`
	Namespaces        []string `json:"namespaces,omitempty"`
	NotNamespaces     []string `json:"notNamespaces,omitempty"`
	RequestPrincipals []string `json:"requestPrincipals,omitempty"`
}

type Operation struct {
	Methods    []string `json:"methods,omitempty"`
	NotMethods []string `json:"notMethods,omitempty"`
	Paths      []string `json:"paths,omitempty"`
	NotPaths   []string `json:"notPaths,omitempty"`
}

type Rule struct {
	From []struct {
		Source Source `json:"source"`
	} `json:"from,omitempty"`
	To []struct {
		Operation Operation `json:"operation"`
	} `json:"to,omitempty"`
}

type AuthorizationPolicy struct {
	Metadata metav1.ObjectMeta `json:"metadata"`
	Spec     struct {
		Selector *WorkloadSelector `json:"selector,omitempty"`
		Action   string            `json:"action,omitempty"` // "" means ALLOW
		Rules    []Rule            `json:"rules,omitempty"`
	} `json:"spec"`
}

type PeerAuthentication struct {
	Metadata metav1.ObjectMeta `json:"metadata"`
	Spec     struct {
		Selector *WorkloadSelector `json:"selector,omitempty"`
		Mtls     *struct {
			Mode string `json:"mode"`
		} `json:"mtls,omitempty"`
	} `json:"spec"`
}

type JWTRule struct {
	Issuer               string   `json:"issuer"`
	JwksURI              string   `json:"jwksUri,omitempty"`
	Audiences            []string `json:"audiences,omitempty"`
	ForwardOriginalToken bool     `json:"forwardOriginalToken,omitempty"`
}

type RequestAuthentication struct {
	Metadata metav1.ObjectMeta `json:"metadata"`
	Spec     struct {
		Selector *WorkloadSelector `json:"selector,omitempty"`
		JWTRules []JWTRule         `json:"jwtRules,omitempty"`
	} `json:"spec"`
}

// ---- Cluster ------------------------------------------------------------------

// Cluster is everything loaded from disk.
type Cluster struct {
	Namespaces             map[string]*corev1.Namespace
	Deployments            map[string]*appsv1.Deployment // key ns/name
	Services               map[string]*corev1.Service    // key ns/name
	AuthorizationPolicies  []*AuthorizationPolicy
	PeerAuthentications    []*PeerAuthentication
	RequestAuthentications []*RequestAuthentication
	Webhooks               []*admissionv1.MutatingWebhookConfiguration
}

// Load reads every *.yaml under root/manifests and root/artifacts/istio.
func Load(root string) (*Cluster, error) {
	c := &Cluster{
		Namespaces:  map[string]*corev1.Namespace{},
		Deployments: map[string]*appsv1.Deployment{},
		Services:    map[string]*corev1.Service{},
	}
	var files []string
	for _, dir := range []string{"manifests", filepath.Join("artifacts", "istio")} {
		err := filepath.WalkDir(filepath.Join(root, dir), func(p string, d os.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if !d.IsDir() && (strings.HasSuffix(p, ".yaml") || strings.HasSuffix(p, ".yml")) {
				files = append(files, p)
			}
			return nil
		})
		if err != nil {
			return nil, err
		}
	}
	sort.Strings(files)
	for _, f := range files {
		b, err := os.ReadFile(f)
		if err != nil {
			return nil, err
		}
		for i, doc := range splitDocs(b) {
			if err := c.add(doc); err != nil {
				return nil, fmt.Errorf("%s doc %d: %w", f, i, err)
			}
		}
	}
	return c, nil
}

func splitDocs(b []byte) [][]byte {
	var out [][]byte
	for _, d := range bytes.Split(b, []byte("\n---")) {
		d = bytes.TrimPrefix(bytes.TrimSpace(d), []byte("---"))
		// skip documents that are only comments
		meaningful := false
		for _, line := range bytes.Split(d, []byte("\n")) {
			t := bytes.TrimSpace(line)
			if len(t) > 0 && t[0] != '#' {
				meaningful = true
				break
			}
		}
		if meaningful {
			out = append(out, d)
		}
	}
	return out
}

func (c *Cluster) add(doc []byte) error {
	var tm metav1.TypeMeta
	if err := yaml.Unmarshal(doc, &tm); err != nil {
		return err
	}
	strict := func(v any) error { return yaml.UnmarshalStrict(doc, v) }
	switch tm.Kind {
	case "Namespace":
		var ns corev1.Namespace
		if err := strict(&ns); err != nil {
			return err
		}
		c.Namespaces[ns.Name] = &ns
	case "Deployment":
		var d appsv1.Deployment
		if err := strict(&d); err != nil {
			return err
		}
		c.Deployments[d.Namespace+"/"+d.Name] = &d
	case "Service":
		var s corev1.Service
		if err := strict(&s); err != nil {
			return err
		}
		c.Services[s.Namespace+"/"+s.Name] = &s
	case "ServiceAccount":
	case "AuthorizationPolicy":
		var p AuthorizationPolicy
		if err := yaml.Unmarshal(doc, &p); err != nil {
			return err
		}
		c.AuthorizationPolicies = append(c.AuthorizationPolicies, &p)
	case "PeerAuthentication":
		var p PeerAuthentication
		if err := yaml.Unmarshal(doc, &p); err != nil {
			return err
		}
		c.PeerAuthentications = append(c.PeerAuthentications, &p)
	case "RequestAuthentication":
		var p RequestAuthentication
		if err := yaml.Unmarshal(doc, &p); err != nil {
			return err
		}
		c.RequestAuthentications = append(c.RequestAuthentications, &p)
	case "MutatingWebhookConfiguration":
		var w admissionv1.MutatingWebhookConfiguration
		if err := yaml.Unmarshal(doc, &w); err != nil {
			return err
		}
		c.Webhooks = append(c.Webhooks, &w)
	default:
		return fmt.Errorf("unsupported kind %q", tm.Kind)
	}
	return nil
}

// ---- Workloads -----------------------------------------------------------------

// Workload is one pod as the mesh sees it.
type Workload struct {
	Namespace      string
	ServiceAccount string
	Labels         map[string]string
	Sidecar        bool
}

// Principal is the SPIFFE identity carried in the peer certificate, or "" for
// plaintext (no sidecar).
func (w Workload) Principal() string {
	if !w.Sidecar {
		return ""
	}
	return "cluster.local/ns/" + w.Namespace + "/sa/" + w.ServiceAccount
}

// FromDeployment returns the workload a newly created pod of ns/name would be.
func (c *Cluster) FromDeployment(ns, name string) (Workload, error) {
	d, ok := c.Deployments[ns+"/"+name]
	if !ok {
		return Workload{}, fmt.Errorf("deployment %s/%s not found", ns, name)
	}
	sa := d.Spec.Template.Spec.ServiceAccountName
	if sa == "" {
		sa = "default"
	}
	return c.Pod(ns, sa, d.Spec.Template.Labels), nil
}

// Pod builds a workload for an arbitrary pod (used for callers with no manifest).
func (c *Cluster) Pod(ns, sa string, podLabels map[string]string) Workload {
	w := Workload{Namespace: ns, ServiceAccount: sa, Labels: podLabels}
	w.Sidecar = c.Injected(ns, podLabels)
	return w
}

// Injected reports whether any installed injector webhook would mutate a pod
// with these labels created in namespace ns.
func (c *Cluster) Injected(ns string, podLabels map[string]string) bool {
	var nsLabels map[string]string
	if n, ok := c.Namespaces[ns]; ok {
		nsLabels = n.Labels
	}
	for _, cfg := range c.Webhooks {
		for _, wh := range cfg.Webhooks {
			if selectorMatches(wh.NamespaceSelector, nsLabels) && selectorMatches(wh.ObjectSelector, podLabels) {
				return true
			}
		}
	}
	return false
}

func selectorMatches(sel *metav1.LabelSelector, l map[string]string) bool {
	if sel == nil {
		return true
	}
	s, err := metav1.LabelSelectorAsSelector(sel)
	if err != nil {
		return false
	}
	return s.Matches(labels.Set(l))
}

// ServiceWorkload returns the workload behind a Service (first matching Deployment).
func (c *Cluster) ServiceWorkload(ns, svc string) (Workload, error) {
	s, ok := c.Services[ns+"/"+svc]
	if !ok {
		return Workload{}, fmt.Errorf("service %s/%s not found", ns, svc)
	}
	keys := make([]string, 0, len(c.Deployments))
	for k := range c.Deployments {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		d := c.Deployments[k]
		if d.Namespace == ns && labels.SelectorFromSet(s.Spec.Selector).Matches(labels.Set(d.Spec.Template.Labels)) {
			return c.FromDeployment(ns, d.Name)
		}
	}
	return Workload{}, fmt.Errorf("service %s/%s has no backing deployment", ns, svc)
}

// ---- Calls --------------------------------------------------------------------

// Result is what the caller and the server-side sidecar access log would show.
type Result struct {
	Status   int    // HTTP status; 0 when the connection was reset
	Details  string // Envoy %RESPONSE_CODE_DETAILS%
	MTLS     bool
	PeerSAN  string // downstream peer principal as seen by the server sidecar
	Response string // body / client-side error
}

func (r Result) String() string {
	if r.Status == 0 {
		return fmt.Sprintf("connection reset (%s) mtls=%v", r.Details, r.MTLS)
	}
	return fmt.Sprintf("%d %s details=%s mtls=%v peer=%q", r.Status, r.Response, r.Details, r.MTLS, r.PeerSAN)
}

// Call models src sending `method path` to the server workload dst.
func (c *Cluster) Call(src, dst Workload, method, path string) Result {
	if !dst.Sidecar {
		return Result{Status: 200, Details: "via_upstream", Response: "OK (no sidecar on server: no policy enforced)"}
	}
	mode := c.peerAuthMode(dst)
	mtls := src.Sidecar // auto-mTLS: client sidecars originate Istio mTLS to meshed servers
	if !mtls && mode == "STRICT" {
		return Result{Status: 0, Details: "filter_chain_not_found", Response: "upstream connect error or disconnect/reset before headers. reset reason: connection termination"}
	}
	r := Result{MTLS: mtls, PeerSAN: src.Principal()}

	// DENY policies first, then ALLOW.
	for _, p := range c.policiesFor(dst) {
		if strings.EqualFold(p.Spec.Action, "DENY") && anyRuleMatches(p.Spec.Rules, src, method, path) {
			r.Status, r.Response = 403, "RBAC: access denied"
			r.Details = fmt.Sprintf("rbac_access_denied_matched_policy[ns[%s]-policy[%s]-rule[0]]", p.Metadata.Namespace, p.Metadata.Name)
			return r
		}
	}
	haveAllow := false
	for _, p := range c.policiesFor(dst) {
		if p.Spec.Action == "" || strings.EqualFold(p.Spec.Action, "ALLOW") {
			haveAllow = true
			if anyRuleMatches(p.Spec.Rules, src, method, path) {
				r.Status, r.Details, r.Response = 200, "via_upstream", "OK"
				return r
			}
		}
	}
	if haveAllow {
		r.Status, r.Response, r.Details = 403, "RBAC: access denied", "rbac_access_denied_matched_policy[none]"
		return r
	}
	r.Status, r.Details, r.Response = 200, "via_upstream", "OK"
	return r
}

func (c *Cluster) policiesFor(dst Workload) []*AuthorizationPolicy {
	var out []*AuthorizationPolicy
	for _, p := range c.AuthorizationPolicies {
		ns := p.Metadata.Namespace
		if ns != dst.Namespace && ns != RootNamespace {
			continue
		}
		if p.Spec.Selector != nil && !labels.SelectorFromSet(p.Spec.Selector.MatchLabels).Matches(labels.Set(dst.Labels)) {
			continue
		}
		out = append(out, p)
	}
	return out
}

// peerAuthMode resolves workload > namespace > mesh-wide; default PERMISSIVE.
func (c *Cluster) peerAuthMode(dst Workload) string {
	mode := func(p *PeerAuthentication) string {
		if p.Spec.Mtls == nil || p.Spec.Mtls.Mode == "" || p.Spec.Mtls.Mode == "UNSET" {
			return ""
		}
		return strings.ToUpper(p.Spec.Mtls.Mode)
	}
	var workload, namespace, mesh string
	for _, p := range c.PeerAuthentications {
		switch {
		case p.Metadata.Namespace == dst.Namespace && p.Spec.Selector != nil:
			if labels.SelectorFromSet(p.Spec.Selector.MatchLabels).Matches(labels.Set(dst.Labels)) {
				workload = mode(p)
			}
		case p.Metadata.Namespace == dst.Namespace:
			namespace = mode(p)
		case p.Metadata.Namespace == RootNamespace && p.Spec.Selector == nil:
			mesh = mode(p)
		}
	}
	for _, m := range []string{workload, namespace, mesh} {
		if m != "" {
			return m
		}
	}
	return "PERMISSIVE"
}

func anyRuleMatches(rules []Rule, src Workload, method, path string) bool {
	for _, r := range rules {
		if ruleMatches(r, src, method, path) {
			return true
		}
	}
	return false
}

// ruleMatches: every field present must match; within a list, any entry matches.
func ruleMatches(r Rule, src Workload, method, path string) bool {
	if len(r.From) > 0 {
		ok := false
		for _, f := range r.From {
			if sourceMatches(f.Source, src) {
				ok = true
				break
			}
		}
		if !ok {
			return false
		}
	}
	if len(r.To) > 0 {
		ok := false
		for _, t := range r.To {
			if operationMatches(t.Operation, method, path) {
				ok = true
				break
			}
		}
		if !ok {
			return false
		}
	}
	return true
}

func sourceMatches(s Source, src Workload) bool {
	p := src.Principal()
	ns := ""
	if p != "" {
		ns = src.Namespace // source.namespaces is derived from the peer certificate
	}
	if len(s.Principals) > 0 && !matchAny(s.Principals, p) {
		return false
	}
	if len(s.NotPrincipals) > 0 && matchAny(s.NotPrincipals, p) {
		return false
	}
	if len(s.Namespaces) > 0 && !matchAny(s.Namespaces, ns) {
		return false
	}
	if len(s.NotNamespaces) > 0 && matchAny(s.NotNamespaces, ns) {
		return false
	}
	if len(s.RequestPrincipals) > 0 {
		return false // the model sends no validated JWT principal
	}
	return true
}

func operationMatches(o Operation, method, path string) bool {
	if len(o.Methods) > 0 && !matchAny(o.Methods, method) {
		return false
	}
	if len(o.NotMethods) > 0 && matchAny(o.NotMethods, method) {
		return false
	}
	if len(o.Paths) > 0 && !matchAny(o.Paths, path) {
		return false
	}
	if len(o.NotPaths) > 0 && matchAny(o.NotPaths, path) {
		return false
	}
	return true
}

// matchAny implements Istio string matching: exact, "*" (any non-empty
// value), "prefix*" and "*suffix". An empty value never matches.
func matchAny(patterns []string, v string) bool {
	if v == "" {
		return false
	}
	for _, p := range patterns {
		switch {
		case p == "*":
			return true
		case strings.HasSuffix(p, "*") && strings.HasPrefix(v, strings.TrimSuffix(p, "*")):
			return true
		case strings.HasPrefix(p, "*") && strings.HasSuffix(v, strings.TrimPrefix(p, "*")):
			return true
		case p == v:
			return true
		}
	}
	return false
}
