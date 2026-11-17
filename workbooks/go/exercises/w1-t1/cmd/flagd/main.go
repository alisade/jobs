// Command flagd serves Corvid Pay feature flags over HTTP.
package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/corvidpay/flagd/internal/flags"
	"github.com/corvidpay/flagd/internal/httpapi"
)

func main() {
	addr := flag.String("addr", "127.0.0.1:8088", "listen address")
	flag.Parse()

	log := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	h := &httpapi.Handler{Svc: &flags.Service{Store: flags.NewMemStore()}, Log: log}
	srv := &http.Server{Addr: *addr, Handler: h.Routes(), ReadHeaderTimeout: 5 * time.Second}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()
	go func() {
		<-ctx.Done()
		shut, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = srv.Shutdown(shut)
	}()

	log.Info("flagd listening", "addr", *addr, "version", "1.14.0")
	if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Error("server failed", "err", err)
		os.Exit(1)
	}
}
