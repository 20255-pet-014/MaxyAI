### Source [1]: https://www.meta-intelligence.tech/en/insight-function-calling

Query: LLM function calling best practices error handling tool use

Answer: LLM Function Calling: OpenAI Tools API, Multi-Step Tool Chains & Error Handling | Meta Intelligence

In June 2023, OpenAI officially launched the Function Calling API(#ref-8), fundamentally changing this landscape. By injecting large quantities of tool invocation training samples during the model fine-tuning phase and combining constrained decoding mechanisms, the model's tool invocation behavior was elevated from "unstructured text guessing" to a "structured API protocol." This technology was quickly adopted by Anthropic, Google, Meta, and other vendors, with Tool Use becoming one of the hottest engineering practices in the LLM field.

### 1.3 Four Major Use Cases for Tool Augmentation [...] ### 3.2 Anthropic Tool Use: Transparent Reasoning with Safety-First Design

Anthropic's Claude designs Tool Use as part of the content block system within the Messages API. Tool definitions are passed as a `tools` array, with a format similar to OpenAI but a fundamentally different return mechanism — tool invocations appear as `tool_use` type content blocks in the assistant message, each containing an independent `id`, `name`, and `input` object. Developers need to return execution results as `tool_result` content blocks, explicitly matching the corresponding invocation with `tool_use_id`.

`tools`
`tool_use`
`id`
`name`
`input`
`tool_result`
`tool_use_id` [...] Function Calling is not just an API feature — it represents a critical turning point in LLM evolution from "language model" to "action agent." Toolformer(#ref-1) proved that models can autonomously learn tool use, Gorilla(#ref-3) and ToolLLM(#ref-2) extended tool-calling capabilities to open-source models, and ReAct(#ref-6) provided a reasoning framework for multi-step tool chains. For enterprises, now is the optimal time to build Function Calling core capabilities — not because the technology is perfect, but because the engineering experience accumulated by early adopters in tool schema design, security architecture construction, and Agent platform development will become an irreplicable competitive moat for future AI-native enterprises.

-----

### Source [3]: https://runloop.ai/blog/mastering-llm-function-calling-a-guide-to-enhancing-ai-capabilities

Query: LLM function calling best practices error handling tool use

Answer: Mastering LLM Function Calling: A Guide to Enhancing AI Capabilities

Robust error handling is also essential for reliable function calling. If a function call fails, the system should be equipped to retry, prompt the user for clarification, or fall back to an alternative tool. Continuous training of LLMs is equally important, as it improves their ability to parse user input and map it to the correct function, reducing errors over time.

Beyond technical challenges, function calling raises ethical considerations. Protecting user privacy is paramount, especially when handling sensitive data like location or payment details. Developers must ensure secure data handling and compliance with regulations like GDPR. [...] A standard for function-calling among all LLMs would reduce variation but the difficulty is currently handled by frameworks like LangChain. LangChain simplifies the integration of LLMs with external tools by providing a unified interface for defining and executing functions. It abstracts away the differences between LLM providers, allowing developers to define tools once and use them across multiple platforms. For example, LangChain can handle variations in function-calling formats between OpenAI and Anthropic, ensuring consistent behavior. It also supports multi-step workflows, error handling, and fallback mechanisms, some of the many reasons it has become the default choice for many developers. Here is LangChain's version of the weather function call.

‍

‍

‍

‍

‍ [...] Another common pitfall is errors in function definitions. Poorly defined tools can result in unexpected behavior and hinder the AI's ability to perform tasks accurately. To mitigate this, it's crucial to provide comprehensive descriptions and input schemas for each tool, ensuring clarity and consistency. Additionally, the LLMs itself has limitations and may struggle with complex or multi-step tasks. Breaking down these tasks into smaller, more manageable steps and utilizing frameworks like LangChain to orchestrate workflows can significantly improve their performance.

-----

### Source [5]: https://aclanthology.org/2025.findings-acl.841.pdf

Query: LLM function calling best practices error handling tool use

Answer: Enhancing Tool Learning in Large Language Models with ...

3.2 HiTEC-ICL: Enhancing LLM Tool Calling in Tuning-free Way We integrate the designed global and local error checklists into the LLM-based tool-calling conver-sation to ensure precise and reliable tool utilization.
The global error checklist is embedded within the user’s initial query at the outset of the inference process. This proactive integration helps preempt common issues, such as tool name misidentifica-tion or parameter omission. By implementing these error prevention mechanisms early in the process, the system significantly enhances the accuracy and reliability of the initial tool invocation. [...] Error 0: Wrong Tool Name Error Error 1: Missing Required Parameter Error Error 2: Invalid Parameter Type Error Error 3: Empty Parameter Value Error Error 4: Redundant Parameter Error Error 5: Invalid Function Calling Output Format Error Error 6: Redundant Information Error Error 7: Wrong Number of Tools Error Please avoid similar errors when making tool calling output.
Figure 3: The Global Error Checklist: a list of common issues that may arise during tool calling ing LLMs specifically for tool calling tasks, they require high-quality training data or extensive tool interaction logs, which are still costly to obtain. [...] Most previous tool learning methods require LLM-tool interactions to improve the calling ac-curacy (Chen et al., 2024a; Qin et al.; Shi et al., 2024; Wang et al., 2024; Yang et al., 2024; Yao et al., 2022; Zhang et al., 2023). For example, STE (Wang et al., 2024) simulate plausible scenarios and incorporates execution feedback to enhance the cor-rect use of tools. It involves first simulating queries, executing real tool calls via tool-LLM interactions, and learning from function calling outputs when er-rors occur. While real-world interactions with tools can yield valuable insights, they cause intensive resources (For example, 10-25$/1,000 transactions for Bing Search API 1) and instability issues (Guo et al., 2024). Furthermore, the errors encountered by most tools called by LLMs are

-----

### Source [7]: https://medium.com/@hariomshahu101/building-production-ready-llm-applications-bulletproof-llm-tool-calling-with-advanced-json-b95ce8889f4e

Query: advanced patterns function calling LLM schema design validation

Answer: Building Production-Ready LLM Applications: Bulletproof LLM Tool Calling with Advanced JSON…

4. Advanced Validation with Pydantic

   Define schema models for each function
   Implement type validation and constraints
   Validate parameter formats (dates, emails, patterns)
   Provide detailed validation error messages

5. Retry with Error Feedback

   Generate specific error context for LLM
   Include function examples and correct schema
   Increase temperature for different JSON generation
   Re-call LLM with corrected instructions

### Stage 3: Tool Execution with Resilience

Objective: Execute validated functions with robust error handling and recovery.

Implementation Steps:

1.   Pre-execution Setup

   Initialize function-specific retry configurations
   Set up monitoring and logging for tool execution
   Prepare fallback strategies for critical functions [...] 1.   Function Existence Verification

   Check if the called function exists in available functions registry
   Validate function name matches exactly (case-sensitive)
   Ensure function is accessible and properly imported

2. JSON Structure Validation

   Parse function arguments from JSON string
   Handle malformed JSON with descriptive error messages
   Validate JSON syntax and structure integrity

3. Parameter Schema Validation

   Extract function signature using introspection
   Identify required vs optional parameters
   Check for missing required parameters
   Validate parameter types and constraints
   Remove unexpected or invalid parameters

4. Advanced Validation with Pydantic [...] Sitemap

Open in app

Sign up

Sign in

"

 }

 },

 "required": ["location"],

 "additionalProperties": false

 }

}
### System Prompt Engineering for Tool Calling:

Respond only with a minified JSON object matching this schema:

'{"location": ""}'

Do not include any Markdown formatting, code block markers, explanations, 

or extra text.

 

You are a function-calling assistant. When calling functions:

1. ALWAYS use the exact parameter names specified in the schema

2. NEVER add extra properties not defined in the schema 

3. ENSURE all required parameters are included

4. VALIDATE parameter types match the schema exactly

5. If unsure about a parameter value, ask for clarification instead of guessing

Example correct function call:

-----

### Source [9]: https://arxiv.org/html/2502.00032v1

Query: advanced patterns function calling LLM schema design validation

Answer: Querying Databases with Function Calling

Tool use is one of the most promising opportunities to improve the capabilities of LLMs. There are two common design patterns for interfacing tool use in Compound AI Systems: Function Calling and Flow Engineering . Visualized in Figure 4, Function Calling entails equipping the LLM with a set of functions described in the prompt. The LLM inference is then orchestrated in a function calling loop. At each step, the LLM either chooses to complete the response, or call one or multiple functions and wait for their respective responses to continue the next iteration of the loop. Contrastively, Flow Engineering describes a pre-determined flow of inferences and external tools calls. This abstraction helps clarify how tools are interfaced to LLMs. However, there is a significant overlap and this is [...] with a searchable text property and three additional properties, one numeric, one textual, and one boolean, to enable comprehensive testing of different query patterns. This structured approach allows us to systematically assess how well LLMs can interpret database schemas and translate natural language requests into appropriate database operations. Given this dataset of schemas, we then create a comprehensive test dataset of queries covering all combinations of query operators defined in the tool schema. These capabilities include search queries for finding relevant results based on relevance ranking algorithms, property filters for matching on integer, text, and boolean fields, aggregations for computing statistics over integer, text, and boolean properties, and grouping operations to

-----
