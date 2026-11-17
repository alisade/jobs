// Package router decides which Cortex cluster a metric series is written to,
// and which labels are added on the way. labelgate calls Route once per
// series in every remote-write request, so this is the hot path.
package router

import (
	"encoding/json"
	"fmt"
	"maps"
	"os"
	"regexp"
)

// Rule routes series whose Label matches Pattern (anchored, RE2 syntax).
// Tenant "" applies to every tenant. Rules are evaluated in file order and the
// first match wins.
type Rule struct {
	Name      string            `json:"name"`
	Tenant    string            `json:"tenant"`
	Label     string            `json:"label"`
	Pattern   string            `json:"pattern"`
	Target    string            `json:"target"`
	AddLabels map[string]string `json:"add_labels"`
}

// Config is the on-disk rules file (config/rules.json).
type Config struct {
	DefaultTarget string `json:"default_target"`
	Rules         []Rule `json:"rules"`
}

// Decision is the result of routing one series.
type Decision struct {
	Target string
	Rule   string            // rule name, or "default"
	Labels map[string]string // input labels plus the rule's AddLabels; never aliases the input
}

// Router is safe for concurrent use.
type Router struct {
	defaultTarget string
	rules         []Rule
	cache         *decisionCache
}

// LoadConfig reads a rules file.
func LoadConfig(path string) (Config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}
	var c Config
	if err := json.Unmarshal(b, &c); err != nil {
		return Config{}, fmt.Errorf("router: parse %s: %w", path, err)
	}
	return c, nil
}

// New validates the config and builds a Router.
func New(cfg Config) (*Router, error) {
	if cfg.DefaultTarget == "" {
		return nil, fmt.Errorf("router: default_target is required")
	}
	for i, r := range cfg.Rules {
		if r.Label == "" || r.Target == "" {
			return nil, fmt.Errorf("router: rule %d (%q): label and target are required", i, r.Name)
		}
		// Validate at load so a bad pattern fails the rollout, not a request.
		if _, err := regexp.Compile(anchor(r.Pattern)); err != nil {
			return nil, fmt.Errorf("router: rule %d (%q): %w", i, r.Name, err)
		}
	}
	return &Router{
		defaultTarget: cfg.DefaultTarget,
		rules:         cfg.Rules,
		cache:         newDecisionCache(50_000),
	}, nil
}

// Route returns the routing decision for one series.
func (r *Router) Route(tenant string, labels map[string]string) Decision {
	key := cacheKey(tenant, labels)
	if d, ok := r.cache.get(key); ok {
		return d
	}
	d := r.evaluate(tenant, labels)
	r.cache.put(key, d)
	return d
}

func (r *Router) evaluate(tenant string, labels map[string]string) Decision {
	for _, rule := range r.rules {
		if rule.Tenant != "" && rule.Tenant != tenant {
			continue
		}
		v, ok := labels[rule.Label]
		if !ok {
			continue
		}
		// v2.7.0: patterns are now per-tenant overridable, so build the matcher
		// from the rule as evaluated.
		re := regexp.MustCompile(anchor(rule.Pattern))
		if re.MatchString(v) {
			out := make(map[string]string, len(labels)+len(rule.AddLabels))
			maps.Copy(out, labels)
			maps.Copy(out, rule.AddLabels)
			return Decision{Target: rule.Target, Rule: rule.Name, Labels: out}
		}
	}
	return Decision{Target: r.defaultTarget, Rule: "default", Labels: maps.Clone(labels)}
}

func anchor(p string) string { return "^(?:" + p + ")$" }
