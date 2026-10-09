// Command snapshot-janitor deletes expired EBS snapshots. It runs as a
// Kubernetes CronJob on EKS and gets AWS credentials from EKS Pod Identity
// through the default credential chain.
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
)

func main() {
	ctx := context.Background()
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		fmt.Fprintln(os.Stderr, "load aws config:", err)
		os.Exit(2)
	}
	_ = ec2.NewFromConfig(cfg)

	// TODO: parse flags matching legacy/snapshot_janitor.py (--owner-id required,
	// --retention-days, --keep-tag, --max-deletes, --dry-run), set up a JSON
	// slog logger, cancel on SIGTERM/SIGINT via signal.NotifyContext, call
	// janitor.Run, log a summary, and exit 1 on ErrPartialFailure, 2 on any
	// other error, 0 on success.
	fmt.Fprintln(os.Stderr, "not implemented")
	os.Exit(2)
}
