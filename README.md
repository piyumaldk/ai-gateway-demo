# WSO2 AI Gateway Demo

A simple demo application to showcase WSO2 AI Gateway guardrail capabilities using Streamlit.

## Configuration

Update [config.py](/Users/tharanikarunathilaka/ai_gateway_demo/config.py) before running the app:

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
streamlit run app.py
```
