Use this policy whenever the user asks for deep research.

1. If the user explicitly says private or open, use that mode.
2. Otherwise ask exactly one question before starting:
   “Should this research run privately through Tinfoil, or openly through OpenRouter?”
3. Private mode may use local files, the local library, internal context, and public web sources.
4. Open mode may receive only the approved question and public context. Do not include local paths, private excerpts, internal notes, personal data, or conversation history that is not part of the public question.
5. Write the approved question to a temporary UTF-8 text file.
6. Run `research-agent run --mode MODE --question-file FILE`.
7. Show the user the preflight estimate and obtain confirmation unless they already explicitly authorized the run and its displayed ceiling.
8. Relay the final report and actual usage. Never silently rerun a failed research job.
