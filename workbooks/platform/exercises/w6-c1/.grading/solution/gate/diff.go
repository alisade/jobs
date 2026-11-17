package gate

import (
	"encoding/json"
	"reflect"
	"sort"
)

// ChangedAttributes returns the top-level attributes whose value differs between Before and
// After, sorted by name. A value is rendered as Sensitive when the matching *_sensitive marker
// is true or contains true anywhere below that attribute.
func ChangedAttributes(rc ResourceChange) []AttrChange {
	before, _ := rc.Change.Before.(map[string]any)
	after, _ := rc.Change.After.(map[string]any)
	names := map[string]bool{}
	for k := range before {
		names[k] = true
	}
	for k := range after {
		names[k] = true
	}
	var out []AttrChange
	for k := range names {
		b, bok := before[k]
		a, aok := after[k]
		if bok == aok && reflect.DeepEqual(b, a) {
			continue
		}
		out = append(out, AttrChange{
			Name:   k,
			Before: render(b, bok, sensitiveAt(rc.Change.BeforeSensitive, k)),
			After:  render(a, aok, sensitiveAt(rc.Change.AfterSensitive, k)),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

func render(v any, present, sensitive bool) string {
	if sensitive {
		return Sensitive
	}
	if !present {
		return "null"
	}
	b, err := json.Marshal(v)
	if err != nil {
		return "?"
	}
	return string(b)
}

func sensitiveAt(marker any, key string) bool {
	switch m := marker.(type) {
	case bool:
		return m
	case map[string]any:
		return anyTrue(m[key])
	}
	return false
}

func anyTrue(v any) bool {
	switch x := v.(type) {
	case bool:
		return x
	case map[string]any:
		for _, e := range x {
			if anyTrue(e) {
				return true
			}
		}
	case []any:
		for _, e := range x {
			if anyTrue(e) {
				return true
			}
		}
	}
	return false
}
