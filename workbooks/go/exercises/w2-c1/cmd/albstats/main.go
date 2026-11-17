// Command albstats summarises ALB access logs per target group.
//
//	aws s3 cp s3://hl-alb-logs/.../file.log.gz - | gunzip | albstats -workers 8
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"text/tabwriter"

	"github.com/harborlane/albstats/alblog"
)

func main() {
	workers := flag.Int("workers", 0, "parser goroutines (0 = GOMAXPROCS)")
	flag.Parse()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	in := os.Stdin
	if flag.NArg() == 1 {
		f, err := os.Open(flag.Arg(0))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		defer f.Close()
		in = f
	}
	rep, err := alblog.Aggregate(ctx, in, *workers)
	if err != nil {
		fmt.Fprintln(os.Stderr, "albstats:", err)
		os.Exit(1)
	}
	tw := tabwriter.NewWriter(os.Stdout, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "TARGET GROUP\tREQUESTS\tELB 5XX\tTARGET 5XX\tP50\tP99")
	for _, g := range rep.Groups {
		fmt.Fprintf(tw, "%s\t%d\t%d\t%d\t%s\t%s\n", g.TargetGroup, g.Requests, g.ELB5xx, g.Target5xx, g.P50, g.P99)
	}
	tw.Flush()
	fmt.Printf("\nlines=%d malformed=%d\n", rep.Lines, rep.Malformed)
	for _, e := range rep.FirstErrors {
		fmt.Println("  ", e)
	}
}
