# Hugging Face LLM Integration Setup Guide

## Overview

The RAG Assistant now uses **Hugging Face Inference API** instead of Ollama for text generation. This allows you to generate answers using state-of-the-art LLMs without needing to download and run them locally.

## Prerequisites

1. **Internet Connection** - Required to call Hugging Face API
2. **Hugging Face Account** - Free account at https://huggingface.co
3. **API Token** - Generate from https://huggingface.co/settings/tokens

## Step 1: Get Hugging Face API Token

1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it: `RAG-Assistant`
4. Role: `read` (reading model weights)
5. Copy the token (starts with `hf_`)

## Step 2: Set Up Environment Variable

### Option A: Using .env file (Recommended)

1. Create `.env` file in project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your token:
```
HF_API_TOKEN=hf_YOUR_TOKEN_HERE
```

3. Python will automatically load it (python-dotenv is installed)

### Option B: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:HF_API_TOKEN="hf_YOUR_TOKEN_HERE"
```

**Windows (Command Prompt):**
```cmd
set HF_API_TOKEN=hf_YOUR_TOKEN_HERE
```

**Linux/Mac:**
```bash
export HF_API_TOKEN="hf_YOUR_TOKEN_HERE"
```

## Step 3: Restart Backend

Kill the current backend process and restart:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

## Step 4: Test in Browser

1. Open: http://localhost:3000
2. Hard refresh: Ctrl+Shift+R
3. Send a query: "How do I fix a 502 error?"
4. Wait for response (first call may take 10-30 seconds)

## Available Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `mistralai/Mistral-7B-Instruct-v0.1` | Fast | Good | Technical support (default) |
| `meta-llama/Llama-2-7b-chat-hf` | Medium | Excellent | Quality-focused tasks |
| `google/flan-t5-base` | Very Fast | Fair | Quick responses |
| `gpt2` | Instant | Poor | Testing only |

### Change Model

Edit `.env`:
```
HF_MODEL=meta-llama/Llama-2-7b-chat-hf
```

Then restart the backend.

## Troubleshooting

### Error: "HF_API_TOKEN environment variable not set"

**Solution:** Make sure you've set the environment variable:
- Check `.env` file exists and has correct token
- Restart the backend after setting token
- Verify token format (should start with `hf_`)

### Error: "Invalid API token"

**Solution:** 
- Go to https://huggingface.co/settings/tokens
- Check token hasn't been revoked
- Generate a new token and update `.env`

### Error: "Model not found" or "Model is currently loading"

**Solution:**
- First call to a model takes time to load (10-30 seconds)
- Wait and try again
- Check model name spelling in `.env`
- Try a smaller model like `google/flan-t5-base`

### Slow Responses (>30 seconds)

**Solution:**
- First request always slower (model loading)
- Subsequent requests faster (cached in Hugging Face)
- Switch to faster model:
  ```
  HF_MODEL=google/flan-t5-base
  ```

## Cost

**Free Tier:**
- Unlimited API calls via inference endpoint
- No credit card required
- Rate limited to prevent abuse

**Paid Options:**
- Upgrade to dedicated inference endpoint for guaranteed speed
- Pricing: ~$9/month per model

## Architecture

```
Frontend → Backend API → Hugging Face Inference API → LLM Model
         ↓
    RRF Search
         ↓
   Firewall Check (confidence > 0.1)
         ↓
    Context Injection
         ↓
    Model Response
```

## Data Privacy

- Requests are sent to Hugging Face servers
- API token is sent with each request (authorization)
- Context chunks are sent to generate answer
- Hugging Face may log API usage (review their privacy policy)
- No data stored permanently on Hugging Face

## Performance Tips

1. **Use cached models** - First call slow, subsequent calls faster
2. **Smaller models faster** - Use `flan-t5` for quick responses
3. **Better models slower** - Use Llama-2 for quality
4. **Batch requests** - Multiple queries work better together

## Switching Back to Ollama

If you later have Ollama available:

1. Edit `app/services/orchestration.py`:
   ```python
   from app.services.llm_integration import OllamaLLM
   # Change to OllamaLLM.build_context() and OllamaLLM.query()
   ```

2. Restart backend

## References

- [Hugging Face Inference API Docs](https://huggingface.co/docs/hub/models-inference)
- [Hugging Face API Console](https://huggingface.co/docs/hub/api-hub)
- [Available Models](https://huggingface.co/models?library=transformers&sort=downloads)

## Support

If you encounter issues:

1. Check `.env` file has correct token
2. Visit https://huggingface.co/settings/tokens to verify token
3. Check internet connection
4. Try a different model
5. Check backend logs for detailed error messages
