// Command audit-sink consumes agent.audit and indexes events into OpenSearch.
package main

import (
	"context"
	"errors"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/relaypoint/audit-sink/internal/sink"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg, err := sink.FromEnv(os.Getenv)
	if err != nil {
		log.Error("config", "err", err)
		os.Exit(2)
	}
	log.Info("starting", "group", cfg.Group, "topic", cfg.Topic, "instance_id", cfg.InstanceID,
		"session_timeout", cfg.SessionTimeout.String())
	cl, err := kgo.NewClient(cfg.Opts()...)
	if err != nil {
		log.Error("client", "err", err)
		os.Exit(2)
	}
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()
	err = sink.Run(ctx, cl, log, func(r *kgo.Record) error { return nil /* index into OpenSearch */ })
	cl.Close()
	if errors.Is(err, sink.ErrFenced) {
		log.Error("fatal: fenced, exiting so the kubelet restarts us", "err", err)
		os.Exit(1)
	}
	if err != nil {
		log.Error("fatal", "err", err)
		os.Exit(1)
	}
}
