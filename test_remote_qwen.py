from batch_sender import make_batch_query

prompts = ["What is the capital of France?"]
responses = make_batch_query(prompts)
for r in responses:
    print(r)