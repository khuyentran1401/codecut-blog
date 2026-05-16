# SlimToolkit Chainlit Chatbot Example

Companion code for [Shrink Your Python Container in One Command with SlimToolkit](../../articles/slimtoolkit_llm_chatbot_container.qmd).

A Chainlit chatbot using the OpenAI SDK, used to demonstrate SlimToolkit's container minification on a realistic LLM-app workload.

## Prerequisites

- Docker
- SlimToolkit (`slim` binary):

  ```bash
  curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash -
  ```

- An OpenAI API key:

  ```bash
  export OPENAI_API_KEY=sk-...
  ```

## 1. Build the fat image

```bash
docker build -t llm-chatbot:fat .
docker images llm-chatbot:fat
```

Expected size: ~308 MB.

## 2. Slim the image

```bash
slim build \
    --target llm-chatbot:fat \
    --tag llm-chatbot:slim \
    --include-path /usr/local/lib/python3.11/site-packages/chainlit \
    --continue-after enter \
    --env OPENAI_API_KEY=$OPENAI_API_KEY
```

When slim pauses after the probe, open `http://localhost:8000`, send a chat message in the browser, then return to the terminal and press Enter so slim records the chat-path files.

Expected size: ~163 MB.

## 3. Run the slim image

```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY llm-chatbot:slim
```

Open `http://localhost:8000` and confirm the chatbot still works.

## 4. (Optional) Compare what got stripped

```bash
slim xray --target llm-chatbot:fat
mv slim.report.json fat.report.json

slim xray --target llm-chatbot:slim

bash compare.sh
```

[`compare.sh`](compare.sh) diffs the two reports and prints the biggest deletions.

## Cleanup

```bash
docker rmi llm-chatbot:fat llm-chatbot:slim
```
