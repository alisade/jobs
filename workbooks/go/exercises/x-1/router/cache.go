package router

import (
	"maps"
	"slices"
	"strings"
	"sync"
)

// decisionCache is a bounded FIFO cache of routing decisions, added in v2.7.0
// to skip rule evaluation for repeated series. Capacity is fixed at
// construction; the oldest entry is evicted when full.
type decisionCache struct {
	mu    sync.Mutex
	cap   int
	items map[string]Decision
	order []string // ring of keys in insertion order
	next  int
}

func newDecisionCache(capacity int) *decisionCache {
	return &decisionCache{cap: capacity, items: make(map[string]Decision, capacity), order: make([]string, 0, capacity)}
}

func (c *decisionCache) get(key string) (Decision, bool) {
	c.mu.Lock()
	d, ok := c.items[key]
	c.mu.Unlock()
	if !ok {
		return Decision{}, false
	}
	d.Labels = maps.Clone(d.Labels) // callers may mutate their copy
	return d, true
}

func (c *decisionCache) put(key string, d Decision) {
	d.Labels = maps.Clone(d.Labels)
	c.mu.Lock()
	defer c.mu.Unlock()
	if _, ok := c.items[key]; ok {
		c.items[key] = d
		return
	}
	if len(c.order) < c.cap {
		c.order = append(c.order, key)
	} else {
		delete(c.items, c.order[c.next])
		c.order[c.next] = key
		c.next = (c.next + 1) % c.cap
	}
	c.items[key] = d
}

func (c *decisionCache) len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return len(c.items)
}

// cacheKey builds tenant\x00k1=v1\x00k2=v2... with keys sorted.
func cacheKey(tenant string, labels map[string]string) string {
	keys := slices.Sorted(maps.Keys(labels))
	var b strings.Builder
	b.WriteString(tenant)
	for _, k := range keys {
		b.WriteByte(0)
		b.WriteString(k)
		b.WriteByte('=')
		b.WriteString(labels[k])
	}
	return b.String()
}
