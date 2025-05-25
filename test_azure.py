import openai
import config

client = openai.AzureOpenAI(
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_KEY,
)

try:
    response = client.chat.completions.create(
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_completion_tokens=10,
        model='gpt-4.1'
    )
    print('Success:', response.choices[0].message.content)
except Exception as e:
    print('Error:', e) 