# Polars Docs Agent with docker-agent

Code for the CodeCut article [Build a Docs Q&A Agent Using docker-agent](https://codecut.ai/docker-agent-docs-qa-rag/).

An agent that answers questions about Polars by searching the Polars user guide. The whole agent is one YAML file.

## Files

```text
docker-agent-docs-qa/
├── embeddings.yaml          # agent with embedding search
├── hybrid.yaml              # same agent with embedding + keyword search
├── evals/
│   ├── asof-join.json       # test: asof join question
│   └── streaming-parquet.json  # test: large Parquet file question
└── setup_docs.sh            # downloads the Polars user guide into docs/polars
```

## Setup

1. Install docker-agent. It ships with Docker Desktop 4.63 and later as `docker agent`. To install it on its own:

   ```bash
   brew install docker-agent
   ```

   The article uses docker-agent v1.150.0. The Homebrew binary is called `docker-agent` and takes the same subcommands as `docker agent`.

2. Export your OpenAI API key. The agent uses OpenAI for both the chat model and the embeddings:

   ```bash
   export OPENAI_API_KEY=your-openai-api-key
   ```

3. Download the Polars user guide (72 markdown files):

   ```bash
   ./setup_docs.sh
   ```

## Run

```bash
docker agent run --exec embeddings.yaml "How do I read a Parquet file without loading it all into memory?"
docker agent run --exec hybrid.yaml "When should I use join_asof?"
```

## Test

The evals run in containers, so Docker must be running:

```bash
docker agent eval hybrid.yaml ./evals
docker agent eval hybrid.yaml ./evals --repeat 3
```

## License

The Polars user guide is MIT licensed: https://github.com/pola-rs/polars
