// Package httpapi exposes the flag service over HTTP.
package httpapi

import (
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"

	"github.com/corvidpay/flagd/internal/flags"
)

// Handler serves /v1/flags.
type Handler struct {
	Svc *flags.Service
	Log *slog.Logger
}

// Routes returns the mux with every route registered (Go 1.22 patterns).
func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	mux.HandleFunc("GET /v1/flags", h.list)
	mux.HandleFunc("GET /v1/flags/{key}", h.get)
	mux.HandleFunc("PUT /v1/flags/{key}", h.put)
	mux.HandleFunc("DELETE /v1/flags/{key}", h.del)
	return mux
}

type errorBody struct {
	Error  string            `json:"error"`
	Fields map[string]string `json:"fields,omitempty"`
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func (h *Handler) list(w http.ResponseWriter, r *http.Request) {
	fs, err := h.Svc.List(r.Context())
	if err != nil {
		h.fail(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, fs)
}

func (h *Handler) get(w http.ResponseWriter, r *http.Request) {
	f, err := h.Svc.Get(r.Context(), r.PathValue("key"))
	if err != nil {
		h.fail(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, f)
}

func (h *Handler) put(w http.ResponseWriter, r *http.Request) {
	var f flags.Flag
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&f); err != nil {
		writeJSON(w, http.StatusBadRequest, errorBody{Error: "invalid JSON: " + err.Error()})
		return
	}
	key := r.PathValue("key")
	if f.Key == "" {
		f.Key = key
	}
	if f.Key != key {
		writeJSON(w, http.StatusBadRequest, errorBody{Error: "body key does not match path"})
		return
	}
	if f.Description == "" {
		h.Log.Debug("flag has no description", "key", f.Key)
	}
	if err := h.Svc.Put(r.Context(), f); err != nil {
		h.fail(w, r, err)
		return
	}
	stored, err := h.Svc.Get(r.Context(), key)
	if err != nil {
		h.fail(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, stored)
}

func (h *Handler) del(w http.ResponseWriter, r *http.Request) {
	if err := h.Svc.Delete(r.Context(), r.PathValue("key")); err != nil {
		h.fail(w, r, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

// fail maps domain errors to status codes.
func (h *Handler) fail(w http.ResponseWriter, r *http.Request, err error) {
	var verr *flags.ValidationError
	switch {
	case errors.Is(err, flags.ErrNotFound):
		writeJSON(w, http.StatusNotFound, errorBody{Error: "flag not found"})
	case errors.As(err, &verr) && len(verr.FieldErrors()) > 0:
		writeJSON(w, http.StatusUnprocessableEntity, errorBody{Error: "validation failed", Fields: verr.FieldErrors()})
	default:
		h.Log.Error("request failed", "method", r.Method, "path", r.URL.Path, "err", err)
		writeJSON(w, http.StatusInternalServerError, errorBody{Error: "internal error"})
	}
}
