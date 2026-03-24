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

Update `config.py` before running the app:

```python
APIM_GATEWAY_AUTH_MODE = "apikey"
APIM_GATEWAY_TOKEN = "your_api_key_here"
```

This app is configured for local APIM access:

- Gateway URL: `https://localhost:8243`
- SSL verification: `APIM_VERIFY_SSL = False`
- Default model: `gpt-4o`

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
