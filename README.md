# WSO2 AI Gateway Demo

A simple demo application to showcase WSO2 AI Gateway guardrail capabilities using Streamlit.

## Prerequisites

- Python 3.9+

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
```

### 2. Activate the virtual environment

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip3 install -r requirements.txt
```

## Configuration

### 1. API Keys

Create `api_keys.py` in the project root with a variable for each API. The variable name must match the `api_key` reference in `config.py`:

```python
APIM4OMINI = "your-api-key-here"
APIM4OMINIPIIMASKINGREGEX = "your-api-key-here"
```

### 2. Gateway Certificate

Copy your gateway's `default-listener.crt` into the `certs/` directory:

```bash
mkdir -p certs
cp /path/to/ai-gateway/resources/certificates/default-listener.crt certs/
```

This enables TLS verification against the gateway's self-signed certificate.

### Settings

- Gateway URL: `https://localhost:8443`
- SSL verification: pinned to `certs/default-listener.crt`
- Auth: `X-API-Key` header (per-API key)
- Default model: `gpt-4`

## Run

Start the Streamlit app:

```bash
source .venv/bin/activate
streamlit run app.py
```

--or-- (windows)

```bash
.venv\Scripts\activate
streamlit run app.py
```

## Deactivate the virtual environment

When done, deactivate the venv:

```bash
deactivate
```
