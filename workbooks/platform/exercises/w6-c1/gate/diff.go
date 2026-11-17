package gate

// ChangedAttributes returns the top-level attributes whose value differs between
// Change.Before and Change.After (both are JSON objects decoded into map[string]any, or nil),
// sorted by name. Values are rendered as compact JSON ("null" when absent). A value is rendered
// as Sensitive ("(sensitive value)") when the matching before_sensitive / after_sensitive
// marker is true, or contains true anywhere below that attribute. Never print a sensitive value.
func ChangedAttributes(rc ResourceChange) []AttrChange {
	// TODO: implement. Hint: reflect.DeepEqual compares decoded JSON values.
	return nil
}
