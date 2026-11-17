// Command labelgate serves the routing API on :8080 and pprof on :6060.
package main

import (
	"flag"
	"log/slog"
	"net/http"
	_ "net/http/pprof"
	"os"

	"github.com/meridian/labelgate/router"
	"github.com/meridian/labelgate/server"
)

func main() {
	rules := flag.String("rules", "config/rules.json", "rules file")
	flag.Parse()
	log := slog.New(slog.NewJSONHandler(os.Stderr, nil))

	cfg, err := router.LoadConfig(*rules)
	if err != nil {
		log.Error("load rules", "err", err)
		os.Exit(1)
	}
	r, err := router.New(cfg)
	if err != nil {
		log.Error("invalid rules", "err", err)
		os.Exit(1)
	}
	go func() { _ = http.ListenAndServe("localhost:6060", nil) }()
	log.Info("listening", "addr", ":8080", "rules", len(cfg.Rules))
	if err := http.ListenAndServe(":8080", server.Handler(r)); err != nil {
		log.Error("serve", "err", err)
		os.Exit(1)
	}
}
