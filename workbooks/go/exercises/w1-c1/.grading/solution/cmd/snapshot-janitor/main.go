// Command snapshot-janitor deletes expired EBS snapshots. It runs as a
// Kubernetes CronJob on EKS and gets AWS credentials from EKS Pod Identity
// through the default credential chain.
package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ec2"

	"github.com/northwind/snapshot-janitor/janitor"
)

func main() { os.Exit(run()) }

func run() int {
	var cfg janitor.Config
	flag.StringVar(&cfg.OwnerID, "owner-id", "", "AWS account id that owns the snapshots (required)")
	flag.IntVar(&cfg.RetentionDays, "retention-days", 30, "delete snapshots older than this")
	flag.StringVar(&cfg.KeepTag, "keep-tag", "retain", "tag key that protects a snapshot when set to true")
	flag.IntVar(&cfg.MaxDeletes, "max-deletes", 200, "safety cap per run (0 = unlimited)")
	flag.BoolVar(&cfg.DryRun, "dry-run", false, "ask EC2 to validate deletes without deleting")
	flag.Parse()

	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	if cfg.OwnerID == "" {
		log.Error("--owner-id is required")
		return 2
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Error("load aws config", "err", err)
		return 2
	}
	res, err := janitor.Run(ctx, ec2.NewFromConfig(awsCfg), cfg)
	log.Info("run finished", "deleted", len(res.Deleted), "skipped", len(res.Skipped),
		"failed", len(res.Failed), "dry_run", cfg.DryRun)
	switch {
	case err == nil:
		return 0
	case errors.Is(err, janitor.ErrPartialFailure):
		log.Error("partial failure", "err", err)
		return 1
	default:
		log.Error("run failed", "err", err)
		return 2
	}
}
