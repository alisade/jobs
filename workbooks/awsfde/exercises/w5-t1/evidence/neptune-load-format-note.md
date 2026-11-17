# From the Neptune docs, "Load format for openCypher data" (excerpt, paraphrased where marked)

- Node files: `:ID` (required), an ID for the node; `:LABEL`, a label for the node.
- "Node IDs should be unique across all node files in the current and previous loads."
- Relationship files: `:ID`, `:START_ID`, `:END_ID`, `:TYPE`.
- Property columns: `name:Type`, for example `name:String`.
