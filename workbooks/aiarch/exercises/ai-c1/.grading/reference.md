# Reference: aiarch/ai-c1

See `.grading/solution/changemgmt/server.py`. Identity is closed over at build time; pydantic
`Annotated[..., Field(...)]` and `Literal` produce both the JSON schema the model sees and the
validation; `ToolAnnotations(read_only_hint=True)` on reads; base64 offset cursor; difflib close
matches for unknown services.
