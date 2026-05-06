import aiohttp
import asyncio

def get_messages(prompt) :
    
    messages = [
        {"role": "system", "content": "You are an expert in databases, relational algebra and formal logic."},
        {"role": "user", "content": prompt}
    ]

    return messages


async def send_prompt(session, prompt):
    
    data = {
        "model": "Qwen3-Coder-30B-A3B-Instruct",
        "messages": get_messages(prompt)
        #"temperature": 0.0,
        #"top_p": 1.0
    }

    url = "http://localhost:8005/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    try:
        # Send the POST request asynchronously
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                return await response.json()  # Parse the JSON response
            else:
                print(f"Error for prompt '{prompt}': Received status code {response.status}")
                print(f"Response: {await response.text()}")
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def send_batch_prompts(prompts):

    async with aiohttp.ClientSession() as session:
        # Create a list of tasks for sending all prompts asynchronously
        tasks = [
            send_prompt(session, prompt)
            for prompt in prompts
        ]

        # Wait for all tasks to complete (barrier synchronization)
        results = await asyncio.gather(*tasks)

    return results

def make_batch_query(prompts):
    results = asyncio.run(send_batch_prompts(prompts))
    output_texts = []
    for result in results:
        if result and "choices" in result and len(result["choices"]) > 0:
            output_texts.append(result["choices"][0]["message"]["content"])
        else:
            output_texts.append("")
    return output_texts
