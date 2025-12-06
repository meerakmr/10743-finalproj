import os
import sys
import config
os.environ['HF_TOKEN'] = config.HF_TOKEN
os.environ['HF_HOME'] = config.HF_HOME

import argparse
import copy
import json
import pandas as pd
import sys
import random
from tqdm import tqdm
import time

from parse_string import LlamaParser
from agents import AgentAction, HuggingfaceChatbot
from utils import *
import random
import numpy as np
import torch

from datasets import Dataset
from datasets import load_dataset, load_from_disk
import config
HF_MCQ_path = config.HF_MCQ_path
dataset_dict = {
    "hard": load_from_disk(os.path.join(HF_MCQ_path, f'MCQ_dict_hard')),
    "easy": load_from_disk(os.path.join(HF_MCQ_path, f'MCQ_dict_easy')),
    "medium": load_from_disk(os.path.join(HF_MCQ_path, f'MCQ_dict_medium'))
}

def set_seeds(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)


def main(args):
    set_seeds(args)
    log(str(args), args.log_path)
    dataset = dataset_dict[args.strategy]
    
    if args.api_name:
        chatbot = ''
    else:    
        chatbot = HuggingfaceChatbot(args.model)
    
    agents = AgentAction(chatbot, 
                         parser_fn = LlamaParser().parse_MCQ,
                         template = args.prompt_template,
                         **vars(args))
    result_save_path = args.log_path.replace('.txt', '_results.txt')

    results = []
    
    # HIPAA only
    domain = 'HIPAA'
    domain_dataset = [item for item in dataset if item.get("domain") == domain]
    
    if args.sample:
        domain_dataset = random.sample(domain_dataset, min(len(domain_dataset), args.sample))
    
    print(f"\n{'='*80}")
    print(f"Running Claude Sonnet on {len(domain_dataset):,} HIPAA MCQs ({args.strategy} difficulty)")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    # Progress bar with time estimation
    pbar = tqdm(enumerate(domain_dataset), total=len(domain_dataset), 
                desc=f"HIPAA {args.strategy.upper()}", 
                unit="mcq", 
                ncols=100,
                bar_format='{desc} | {percentage:3.0f}% {bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {rate_fmt}')
    
    for i, item in pbar:
        label = item['label']
        decision = {}
        log(str(f"=== domain: {domain} --- case: {i}\n"), args.log_path)
        
        for _ in range(args.generation_round):
            try:
                decision = agents.complete(**item)           
                result = (decision["decision"] == label)
                results.append(result)
                acc = (sum(results) / len(results))
                
                # Update progress bar with accuracy
                pbar.set_postfix({'accuracy': f'{acc:.3f}'})
                log(str(f"sample_id: {i} --- result:{result} --- answer: {decision['decision']}\n"), args.log_path)
                log(str(decision)+"\n", args.log_path)
                
                if decision: 
                    break

            except Exception as e:
                print(f"\nError: {e}")
                log(str(f"Error at sample {i}: {e}\n"), args.log_path)
                continue
        
        if not decision: 
            results.append(0)

    pbar.close()
    
    # Final results
    end_time = time.time()
    total_time = end_time - start_time
    minutes = total_time / 60
    hours = minutes / 60
    
    acc = (sum(results) / len(results))
    
    print(f"\n{'='*80}")
    print(f"HIPAA MCQ Evaluation Complete")
    print(f"{'='*80}")
    print(f"Domain:        {domain}")
    print(f"Difficulty:    {args.strategy.upper()}")
    print(f"Total MCQs:    {len(domain_dataset):,}")
    print(f"Accuracy:      {acc:.2%}")
    print(f"Time elapsed:  {hours:.2f} hours ({minutes:.1f} minutes, {total_time:.0f} seconds)")
    print(f"Rate:          {len(domain_dataset) / total_time:.2f} MCQ/sec")
    print(f"{'='*80}\n")
    
    log(str(f"domain: {domain} --- num_sample: {len(domain_dataset)} --- accuracy:{acc}\n"), args.log_path)
    log(str(f"domain: {domain} --- num_sample: {len(domain_dataset)} --- accuracy:{acc}\n"), result_save_path)
    log(str(f"Total time: {hours:.2f} hours ({minutes:.1f} minutes)\n"), args.log_path)
    log(str(f"Total time: {hours:.2f} hours ({minutes:.1f} minutes)\n"), result_save_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate Claude on HIPAA MCQs')
    parser.add_argument("--model", type=str, default="")
    parser.add_argument("--log_path", type=str, default="logs/MCQ_hipaa_claude.txt")
    parser.add_argument("--strategy", type=str, default='medium', 
                        help="Difficulty level: easy, medium, or hard")
    parser.add_argument("--prompt_template", type=str, default="prompts/MCQ_template.txt")
    parser.add_argument("--max_new_tokens", type=int, default=1024)

    parser.add_argument("--generation_round", type=int, default=10)
    parser.add_argument("--max_law_items", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--api_name", type=str, default='claude',
                        help="API name: 'claude' for Anthropic Claude")
    parser.add_argument("--api_model", type=str, default='claude-sonnet-4-20250514',
                        help="Claude model version")
    parser.add_argument("--api_token", type=str, default='',
                        help="Anthropic API key")
    parser.add_argument("--sample", type=int, default=None,
                        help="Sample N MCQs per domain (default: all)")
    parser.add_argument("--max_retry", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.2)
    
    args = parser.parse_args()
    
    # Use environment variable if token not provided
    if not args.api_token:
        args.api_token = os.getenv('ANTHROPIC_API_KEY', '')
        if not args.api_token:
            print("Error: ANTHROPIC_API_KEY not set. Please provide --api_token or set ANTHROPIC_API_KEY env var")
            sys.exit(1)
    
    main(args)
