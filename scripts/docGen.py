from transformers import pipeline, logging, AutoTokenizer, TextStreamer
import os
import time
from datetime import datetime
import argparse
import torch

# export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# parse arguments
parser = argparse.ArgumentParser(description="Generates military documents via an LLM based on user input")
parser.add_argument("-t", "--max-tokens", type=int, help="Specify the max number of tokens when generating the document, default is 500", default=500)
args = parser.parse_args()

model = "meta-llama/Llama-3.1-8B-Instruct"

# generator = pipeline("text-generation", model="meta-llama/Llama-3.2-11B-Vision-Instruct", device=device, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model)
streamer = TextStreamer(tokenizer, skip_prompt=True)
generator = pipeline("text-generation", model, tokenizer=tokenizer, device_map="auto", torch_dtype=torch.float16)
logging.set_verbosity_error()

def clean_output(text: str) -> str:
    return text.rsplit("Example:")[0]

# get document type from user
doc = int(input("Select document to generate\n1) Naval Message (NAVADMIN)\n2) USMC Message (MARADMIN)\n3) USMC OpOrd\n> "))
type = ""

match doc:
    case 1:
        type = "NAVADMIN"
    case 2:
        type = "MARADMIN"
    case 3:
        type = "OpOrd"
    case _:
        type = "NAVADMIN"

# define pieces of prompt
role = "Role: You work for the United States Department of the Navy, and you specialize in writing official military documents using military formatting.\n"

# load in examples for few shot prompting
examples = "Read the following examples very carefully. Your response must follow the same formatting as these examples.\n"

data_path = "../data"
files = []

# get paths to all example files
for root, dirs, fnames in os.walk(data_path):
    for f in fnames:
        if type in f:
            files.append(os.path.join(root, f))

# append contents of each file to examples
for f in files:
    with open(f, 'r') as file:
        examples += f"Example:\n {file.read()}\n\n"
        
user_query = input("Input> ")
user_query = "Request: " + user_query
format = "Give your answer in naval message format based on the previous examples."

prompt = role + examples + user_query + format

t_start = time.time()
response = generator(prompt, max_new_tokens=args.max_tokens, streamer=streamer)[0]['generated_text'][len(prompt):]
t_stop = time.time()

print(f"Generation time: {t_stop - t_start}")

# save response to file
fname = datetime.now().strftime("%d-%b-%Y_%H:%M:%S")
path = f"../output/{fname}.txt"
with open(path, 'w') as file:
    file.write(f"---------- RESPONSE ----------\n{response}\n\n")
    file.write(f"---------- PROMPT ----------\n{prompt}")