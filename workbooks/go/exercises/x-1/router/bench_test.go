package router

import (
	"fmt"
	"testing"
)

// go test -run XXX -bench . -benchmem ./router
func BenchmarkRouteCacheMiss(b *testing.B) {
	cfg, err := LoadConfig("../config/rules.json")
	if err != nil {
		b.Fatal(err)
	}
	r, err := New(cfg)
	if err != nil {
		b.Fatal(err)
	}
	b.ReportAllocs()
	i := 0
	for b.Loop() {
		i++
		r.Route("payments", map[string]string{"namespace": "sandbox-1", "pod": fmt.Sprint(i), "job": "x"})
	}
}
