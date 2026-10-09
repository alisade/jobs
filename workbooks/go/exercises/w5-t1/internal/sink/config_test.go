package sink

import (
	"slices"
	"testing"
	"time"
)

func envMap(m map[string]string) func(string) string { return func(k string) string { return m[k] } }

func TestFromEnvDefaultsAndBrokers(t *testing.T) {
	c, err := FromEnv(envMap(map[string]string{
		"KAFKA_BROKERS":     "b-1:9098, b-2:9098,,b-3:9098",
		"GROUP_INSTANCE_ID": "audit-sink-1",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(c.Brokers, []string{"b-1:9098", "b-2:9098", "b-3:9098"}) {
		t.Fatalf("Brokers = %v", c.Brokers)
	}
	if c.Group != "audit-sink" || c.Topic != "agent.audit" {
		t.Fatalf("defaults: group=%q topic=%q", c.Group, c.Topic)
	}
	if c.SessionTimeout != 45*time.Second || c.RebalanceTimeout != 60*time.Second {
		t.Fatalf("timeouts: %s %s", c.SessionTimeout, c.RebalanceTimeout)
	}
	if !c.StaticMembership || c.InstanceID != "audit-sink-1" {
		t.Fatalf("static membership: %v %q", c.StaticMembership, c.InstanceID)
	}
}

func TestFromEnvRequiresBrokers(t *testing.T) {
	if _, err := FromEnv(envMap(nil)); err == nil {
		t.Fatal("want error without KAFKA_BROKERS")
	}
}

func TestFromEnvBadDuration(t *testing.T) {
	_, err := FromEnv(envMap(map[string]string{"KAFKA_BROKERS": "b:1", "GROUP_INSTANCE_ID": "x", "KAFKA_SESSION_TIMEOUT": "2 minutes"}))
	if err == nil {
		t.Fatal("want error for an unparsable duration")
	}
}
