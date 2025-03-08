import asyncio
import time
from queue import Queue
from typing import Tuple

from config import logger, openai_client as client, MODELS


async def get_model_response(
    question: str, options: str, model: str
) -> Tuple[bool, str, float]:
    MAX_RETRIES = 2
    start_time = time.perf_counter()
    logger.info(f"Getting response from model: {model}")

    def validate_answer(ans: str, is_mcq: bool) -> bool:
        if not ans:
            return False
        if is_mcq:
            return len(ans.strip()) == 1 and ans.strip().upper() in ["A", "B", "C", "D"]
        return len(ans.split()) > 0

    try:
        for attempt in range(MAX_RETRIES + 1):
            if options:
                prompt = f"""Multiple Choice Question:
{question}
{options}

Instructions:
1. ONLY respond with the letter (A, B, C, or D) of the correct option
2. Do not write the full answer or any explanation
3. Just the letter, nothing else

You must respond with just A, B, C, or D."""
            else:
                prompt = f"""Answer this question concisely:
{question}

Instructions:
1. If it's a factual question (like capitals, dates, names), give the exact correct answer
2. The answer must be brief and to the point - avoid explanations or unnecessary words
3. Proper nouns should be capitalized (e.g., Delhi, Paris, Einstein)
4. Keep your response very short and focused

Your response must be clear and concise."""

            try:
                logger.debug(
                    f"Attempt {attempt + 1}/{MAX_RETRIES + 1} for model {model}"
                )
                completion = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a precise answering system that follows instructions exactly.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                    ),
                )
                answer = completion.choices[0].message.content.strip()

                if validate_answer(answer, bool(options)):
                    elapsed_time = time.perf_counter() - start_time
                    logger.info(f"Valid response from {model} in {elapsed_time:.2f}s")
                    return True, answer.upper() if options else answer, elapsed_time

                if attempt < MAX_RETRIES:
                    continue

                return True, "Invalid response" if options else "Unknown", elapsed_time

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {model}: {str(e)}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
                    continue
                raise e
    except Exception as e:
        elapsed_time = time.perf_counter() - start_time
        logger.error(f"All attempts failed for {model}: {str(e)}")
        return False, f"Error ({model.split('/')[-1]}): {str(e)}", elapsed_time


async def get_all_model_responses(
    question: str, options: str, result_queue: Queue
) -> None:
    responses = {model: ("-", 0.0) for model in MODELS}
    result_queue.put(("partial", responses.copy()))

    async def process_model(model):
        result = await get_model_response(question, options, model)
        if isinstance(result, tuple) and result[0]:
            responses[model] = (result[1], result[2])
        elif isinstance(result, Exception):
            responses[model] = (f"Error: {str(result)}", 0.0)
        else:
            responses[model] = (f"Error: Failed to get response", 0.0)
        result_queue.put(("partial", responses.copy()))

    tasks = [process_model(model) for model in MODELS]
    await asyncio.gather(*tasks)
    result_queue.put(("complete", responses))
