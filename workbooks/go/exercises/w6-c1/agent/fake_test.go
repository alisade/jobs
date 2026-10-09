package agent

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

// fakeAPI is a scripted stand-in for POST /v1/messages. Each request consumes
// the next step. It records every request body so tests can assert on the shape
// of what the agent sent. No real API is ever called.
type fakeAPI struct {
	t     *testing.T
	mu    sync.Mutex
	steps []step
	reqs  []apiRequest
	srv   *httptest.Server
}

type step struct {
	status int    // 0 means 200
	body   string // JSON response body
}

// apiRequest is the subset of the Messages API request the tests look at.
type apiRequest struct {
	Model     string `json:"model"`
	MaxTokens int64  `json:"max_tokens"`
	System    []struct {
		Text string `json:"text"`
	} `json:"system"`
	Tools []struct {
		Name        string         `json:"name"`
		Description string         `json:"description"`
		InputSchema map[string]any `json:"input_schema"`
	} `json:"tools"`
	Messages []struct {
		Role    string         `json:"role"`
		Content []contentBlock `json:"content"`
	} `json:"messages"`
}

type contentBlock struct {
	Type      string          `json:"type"`
	Text      string          `json:"text"`
	ID        string          `json:"id"`
	Name      string          `json:"name"`
	Input     json.RawMessage `json:"input"`
	ToolUseID string          `json:"tool_use_id"`
	IsError   bool            `json:"is_error"`
	Content   []struct {
		Type string `json:"type"`
		Text string `json:"text"`
	} `json:"content"`
}

// resultText returns the text of a tool_result block.
func (c contentBlock) resultText() string {
	s := ""
	for _, p := range c.Content {
		s += p.Text
	}
	return s
}

func newFake(t *testing.T, steps ...step) *fakeAPI {
	t.Helper()
	f := &fakeAPI{t: t, steps: steps}
	f.srv = httptest.NewServer(http.HandlerFunc(f.serve))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeAPI) serve(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || r.URL.Path != "/v1/messages" {
		http.Error(w, `{"type":"error","error":{"type":"not_found_error","message":"unexpected path"}}`, http.StatusNotFound)
		return
	}
	raw, _ := io.ReadAll(r.Body)
	var req apiRequest
	if err := json.Unmarshal(raw, &req); err != nil {
		f.t.Errorf("fake: request is not JSON: %v", err)
	}
	f.mu.Lock()
	f.reqs = append(f.reqs, req)
	n := len(f.reqs)
	var s step
	if n <= len(f.steps) {
		s = f.steps[n-1]
	} else {
		s = step{status: 500, body: `{"type":"error","error":{"type":"api_error","message":"fake: script exhausted"}}`}
	}
	f.mu.Unlock()
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("request-id", fmt.Sprintf("req_fake_%d", n))
	if s.status != 0 {
		w.WriteHeader(s.status)
	}
	_, _ = io.WriteString(w, s.body)
}

func (f *fakeAPI) requests() []apiRequest {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]apiRequest(nil), f.reqs...)
}

// client returns an SDK client pointed at the fake, with retries off.
func (f *fakeAPI) client() anthropic.Client {
	return anthropic.NewClient(
		option.WithBaseURL(f.srv.URL),
		option.WithAPIKey("sk-ant-test-not-a-real-key"),
		option.WithMaxRetries(0),
	)
}

// ---- response builders --------------------------------------------------

type toolUse struct {
	ID, Name, Input string // Input is a JSON object literal
}

func msgJSON(stop string, in, out int64, blocks ...string) step {
	content := "["
	for i, b := range blocks {
		if i > 0 {
			content += ","
		}
		content += b
	}
	content += "]"
	return step{body: fmt.Sprintf(`{"id":"msg_fake","type":"message","role":"assistant","model":"claude-sonnet-5-5",`+
		`"content":%s,"stop_reason":%q,"stop_sequence":null,`+
		`"usage":{"input_tokens":%d,"output_tokens":%d,"cache_creation_input_tokens":0,"cache_read_input_tokens":0}}`,
		content, stop, in, out)}
}

func textBlock(s string) string {
	b, _ := json.Marshal(map[string]string{"type": "text", "text": s})
	return string(b)
}

func toolBlock(u toolUse) string {
	return fmt.Sprintf(`{"type":"tool_use","id":%q,"name":%q,"input":%s}`, u.ID, u.Name, u.Input)
}

// toolTurn: the model asks for one or more tools.
func toolTurn(in, out int64, preamble string, uses ...toolUse) step {
	blocks := []string{}
	if preamble != "" {
		blocks = append(blocks, textBlock(preamble))
	}
	for _, u := range uses {
		blocks = append(blocks, toolBlock(u))
	}
	return msgJSON("tool_use", in, out, blocks...)
}

// finalTurn: the model answers.
func finalTurn(in, out int64, text string) step {
	return msgJSON("end_turn", in, out, textBlock(text))
}
