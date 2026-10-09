// Package sink consumes agent audit events from Kafka and indexes them.
package sink

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/twmb/franz-go/pkg/kgo"
)

// Config is the consumer configuration, read from the pod environment.
type Config struct {
	Brokers          []string
	Group            string
	Topic            string
	StaticMembership bool
	InstanceID       string // group.instance.id (KIP-345) when StaticMembership is true
	SessionTimeout   time.Duration
	RebalanceTimeout time.Duration
}

// FromEnv builds a Config. getenv is os.Getenv in production and a map lookup in tests.
//
//	KAFKA_BROKERS            comma-separated, required
//	KAFKA_GROUP              default "audit-sink"
//	KAFKA_TOPIC              default "agent.audit"
//	KAFKA_STATIC_MEMBERSHIP  "true" (default) or "false"
//	GROUP_INSTANCE_ID        group.instance.id when static membership is on
//	KAFKA_SESSION_TIMEOUT    Go duration, default 45s
//	KAFKA_REBALANCE_TIMEOUT  Go duration, default 60s
func FromEnv(getenv func(string) string) (Config, error) {
	c := Config{
		Group:            or(getenv("KAFKA_GROUP"), "audit-sink"),
		Topic:            or(getenv("KAFKA_TOPIC"), "agent.audit"),
		StaticMembership: getenv("KAFKA_STATIC_MEMBERSHIP") != "false",
	}
	for _, b := range strings.Split(getenv("KAFKA_BROKERS"), ",") {
		if b = strings.TrimSpace(b); b != "" {
			c.Brokers = append(c.Brokers, b)
		}
	}
	if len(c.Brokers) == 0 {
		return Config{}, errors.New("KAFKA_BROKERS is required")
	}
	var err error
	if c.SessionTimeout, err = duration(getenv("KAFKA_SESSION_TIMEOUT"), 45*time.Second); err != nil {
		return Config{}, fmt.Errorf("KAFKA_SESSION_TIMEOUT: %w", err)
	}
	if c.RebalanceTimeout, err = duration(getenv("KAFKA_REBALANCE_TIMEOUT"), 60*time.Second); err != nil {
		return Config{}, fmt.Errorf("KAFKA_REBALANCE_TIMEOUT: %w", err)
	}
	if c.StaticMembership {
		c.InstanceID = getenv("GROUP_INSTANCE_ID")
		if c.InstanceID == "" {
			// Keep local docker-compose runs working without extra env.
			c.InstanceID = "audit-sink-0"
		}
	}
	return c, nil
}

// Opts converts the Config to franz-go client options.
func (c Config) Opts() []kgo.Opt {
	opts := []kgo.Opt{
		kgo.SeedBrokers(c.Brokers...),
		kgo.ConsumerGroup(c.Group),
		kgo.ConsumeTopics(c.Topic),
		kgo.SessionTimeout(c.SessionTimeout),
		kgo.RebalanceTimeout(c.RebalanceTimeout),
		kgo.DisableAutoCommit(),
	}
	if c.StaticMembership && c.InstanceID != "" {
		opts = append(opts, kgo.InstanceID(c.InstanceID))
	}
	return opts
}

func or(v, def string) string {
	if v == "" {
		return def
	}
	return v
}

func duration(v string, def time.Duration) (time.Duration, error) {
	if v == "" {
		return def, nil
	}
	return time.ParseDuration(v)
}
