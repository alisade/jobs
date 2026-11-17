// Package podsim renders the audit-sink workload from deploy/audit-sink.yaml
// into per-replica pod names and environments, the way the kubelet would
// resolve them. It is only used by cmd/repro to replay the incident locally.
package podsim

import (
	"bytes"
	"fmt"
	"hash/fnv"
	"os"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/yaml"
)

// Replica is one simulated pod.
type Replica struct {
	PodName string
	Env     map[string]string
}

// Render returns the replicas of the audit-sink workload. rollout distinguishes
// successive rollouts/restarts: Deployment pod names change with it,
// StatefulSet pod names do not.
func Render(path string, rollout int) (kind string, reps []Replica, err error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", nil, err
	}
	for _, doc := range bytes.Split(raw, []byte("\n---")) {
		var meta struct {
			Kind string `json:"kind"`
		}
		if yaml.Unmarshal(doc, &meta) != nil {
			continue
		}
		var name, ns string
		var replicas int32 = 1
		var tmpl corev1.PodTemplateSpec
		switch meta.Kind {
		case "Deployment":
			var d appsv1.Deployment
			if err := yaml.Unmarshal(doc, &d); err != nil {
				return "", nil, err
			}
			name, ns, tmpl = d.Name, d.Namespace, d.Spec.Template
			if d.Spec.Replicas != nil {
				replicas = *d.Spec.Replicas
			}
		case "StatefulSet":
			var s appsv1.StatefulSet
			if err := yaml.Unmarshal(doc, &s); err != nil {
				return "", nil, err
			}
			name, ns, tmpl = s.Name, s.Namespace, s.Spec.Template
			if s.Spec.Replicas != nil {
				replicas = *s.Spec.Replicas
			}
		default:
			continue
		}
		for i := 0; i < int(replicas); i++ {
			pod := fmt.Sprintf("%s-%d", name, i)
			if meta.Kind == "Deployment" {
				pod = fmt.Sprintf("%s-%s-%s", name, hash(fmt.Sprint(rollout), 10), hash(fmt.Sprint(rollout, i), 5))
			}
			reps = append(reps, Replica{PodName: pod, Env: resolveEnv(tmpl, pod, ns)})
		}
		return meta.Kind, reps, nil
	}
	return "", nil, fmt.Errorf("%s: no Deployment or StatefulSet found", path)
}

func resolveEnv(t corev1.PodTemplateSpec, pod, ns string) map[string]string {
	env := map[string]string{}
	for _, c := range t.Spec.Containers {
		if c.Name != "audit-sink" {
			continue
		}
		for _, e := range c.Env {
			switch {
			case e.ValueFrom == nil:
				env[e.Name] = e.Value
			case e.ValueFrom.FieldRef != nil && e.ValueFrom.FieldRef.FieldPath == "metadata.name":
				env[e.Name] = pod
			case e.ValueFrom.FieldRef != nil && e.ValueFrom.FieldRef.FieldPath == "metadata.namespace":
				env[e.Name] = ns
			}
		}
	}
	return env
}

func hash(s string, n int) string {
	const alphabet = "bcdfghjklmnpqrstvwxz2456789"
	h := fnv.New64a()
	h.Write([]byte(s))
	v := h.Sum64()
	out := make([]byte, n)
	for i := range out {
		out[i] = alphabet[v%uint64(len(alphabet))]
		v /= uint64(len(alphabet))
		if v == 0 {
			v = h.Sum64() + uint64(i)
		}
	}
	return string(out)
}
