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

### Source [2]: https://mbrenndoerfer.com/writing/function-calling-llm-structured-tools

Query: LLM function calling best practices error handling tool use

Answer: Function Calling: Structured Tool Use for LLMs - Interactive | Michael Brenndoerfer

Cumulative token consumption across function calling iterations, illustrating how tool calls and observations accumulate in the context window. Starting from an initial system and user message of around 920 tokens, each tool call and observation cycle adds approximately 600 tokens. A dashed red line marks a typical 4096-token context limit, showing how multi-step tool use can rapidly approach capacity.

### Error HandlingLink Copied

Not all function calls succeed. Networks fail, APIs return errors, and arguments may be invalid. The error handling strategy significantly affects reliability and user experience. A brittle system that crashes on API timeouts provides little value, while a resilient system that gracefully degrades maintains utility even under adverse conditions. [...] Retry with correction: Present the error to the model and allow it to generate a corrected call. For example, if a weather API returns "Location not found" for "Bostn, MA", the model might infer the typo and retry with "Boston, MA". This requires the error message to be descriptive enough to enable diagnostic reasoning.
 Fallback to knowledge: If the tool fails, the model falls back to its parametric knowledge with appropriate uncertainty qualifiers. For instance, "I was unable to check the live weather, but based on my training data, Boston in January is typically cold, often below freezing." This maintains utility while signaling uncertainty. [...] Practical deployment demands attention to error handling, security validation, latency optimization, and context window management. Production systems must guard against injection attacks, handle API failures gracefully, and manage the computational costs of multi-turn interactions.

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

### Source [4]: https://community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036

Query: LLM function calling best practices error handling tool use

Answer: Prompting Best Practices for Tool Use (Function Calling) - Prompting - OpenAI Developer Community

# Prompting Best Practices for Tool Use (Function Calling)

I’m looking for an explanation of how LLMs use/see the information passed in to the API parameters - specifically the tools that are specified.

When specifying a list of tools in the parameters to the API request, is it still necessary to declare and describe the list of tools in the system prompt? If so, why? Can’t the LLM see that I declared the list in the parameters? I can even pass in a description field in the JSON definitions of the tools. So do I still need to mention them in the prompt? If so, why?

Hello, let me break it down…

The language model only processes the text in the conversation.

Data in API parameters, like tool definitions and descriptions, are not automatically added to the text the model sees. [...] Appreciate both the responses. Although they’re saying quite opposite things.  
It’ll be very easy to prove which is correct. I’ll do a test where I provide an LLM with some tools in the parameters to the request, don’t mention it in the prompt, and ask it what/if any tools it has access to. I’ll report back what I find.

Since the LLM doesn’t actually directly reach out to your tools and make function calls, it seems to me like there would be no other point in passing them into the request params if they weren’t being directly passed to the LLM as a way of informing the LLM about what tools are available. What other purpose would they serve?

don’t mention it in the prompt, and ask it what/if any tools it has access to

Wait, that’s not what you asked and I made no statement on that. [...] You need to include tool details in the system prompt if you want the model to reference them during its response.

The JSON definitions serve the API or middleware, but the model relies on explicit text in its context.

Hope that helps!

is it still necessary to declare and describe the list of tools in the system prompt?

No, but sometimes it helps to “emphasise” their presence or the presence of specific functions you wish to “prioritise”.

The system prompt is a lot about “emphasis” in general.

I can even pass in a description field in the JSON definitions of the tools

Yes you can.

image

image

Can’t the LLM see that I declared the list in the parameters?

So yes, you don’t have to mention them in the system prompt at all.

-----

### Source [5]: https://aclanthology.org/2025.findings-acl.841.pdf

Query: LLM function calling best practices error handling tool use

Answer: Enhancing Tool Learning in Large Language Models with ...

3.2 HiTEC-ICL: Enhancing LLM Tool Calling in Tuning-free Way We integrate the designed global and local error checklists into the LLM-based tool-calling conver-sation to ensure precise and reliable tool utilization.
The global error checklist is embedded within the user’s initial query at the outset of the inference process. This proactive integration helps preempt common issues, such as tool name misidentifica-tion or parameter omission. By implementing these error prevention mechanisms early in the process, the system significantly enhances the accuracy and reliability of the initial tool invocation. [...] Error 0: Wrong Tool Name Error Error 1: Missing Required Parameter Error Error 2: Invalid Parameter Type Error Error 3: Empty Parameter Value Error Error 4: Redundant Parameter Error Error 5: Invalid Function Calling Output Format Error Error 6: Redundant Information Error Error 7: Wrong Number of Tools Error Please avoid similar errors when making tool calling output.
Figure 3: The Global Error Checklist: a list of common issues that may arise during tool calling ing LLMs specifically for tool calling tasks, they require high-quality training data or extensive tool interaction logs, which are still costly to obtain. [...] Most previous tool learning methods require LLM-tool interactions to improve the calling ac-curacy (Chen et al., 2024a; Qin et al.; Shi et al., 2024; Wang et al., 2024; Yang et al., 2024; Yao et al., 2022; Zhang et al., 2023). For example, STE (Wang et al., 2024) simulate plausible scenarios and incorporates execution feedback to enhance the cor-rect use of tools. It involves first simulating queries, executing real tool calls via tool-LLM interactions, and learning from function calling outputs when er-rors occur. While real-world interactions with tools can yield valuable insights, they cause intensive resources (For example, 10-25$/1,000 transactions for Bing Search API 1) and instability issues (Guo et al., 2024). Furthermore, the errors encountered by most tools called by LLMs are

-----

### Source [6]: https://medium.com/aimonks/the-llm-function-design-pattern-a-structured-approach-to-ai-powered-software-development-f4192945d5f4

Query: advanced patterns function calling LLM schema design validation

Answer: The LLM Function Design Pattern: A Structured Approach to AI-Powered ...

Advantages include:

In environments where the LLM supports function calling or structured outputs, this pattern aligns naturally. Most such systems require a valid JSON schema that describes the expected output format. Java record types — being immutable, flat, and well-typed — can be automatically converted into JSON schemas using standard libraries. These schemas can then be attached to the LLM request to constrain the model’s output generation.

This provides a second layer of validation: the model is not only prompted to return structured output but is also given an explicit target schema to match. This approach is particularly effective when working with OpenAI function calling, Claude tool use, or similar features from other LLM providers.

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

### Source [8]: https://medium.com/@chiwai.kiriba/what-is-json-schema-validation-26b81659419d

Query: advanced patterns function calling LLM schema design validation

Answer: Medium

Useful practices include:

   Document each field clearly.
   Use enums when only specific values are allowed.
   Use patterns for strict formats such as IDs, dates, and emails.
   Combine schema validation with application-level validation.
   Test valid inputs, invalid inputs, missing fields, and edge cases before deployment.

JSON schema validation makes LLM function calling more dependable by turning model output into structured and controlled input. It prevents malformed requests, reduces runtime failures, improves debugging, and helps protect the application from unexpected behavior. When schemas are clear, tested, and supported by deeper validation layers, AI systems become more reliable in real production workflows.

Large Language Models

Machine Learning Ai

Json

Big Data [...] In LLM-based systems, the model may generate a function call based on a user request, but that output should not be trusted blindly. The system needs a validation layer that checks whether the generated JSON matches the expected schema. When this is done properly, function calling becomes more consistent, safer, and easier to debug.

## Why JSON Schema Validation Matters

Without schema validation, LLM-generated function calls can become unreliable. A model may omit important parameters, use the wrong data type, provide an unsupported value, or include extra fields that the function was not designed to handle. These mistakes can break workflows, cause failed API calls, or create security risks in production systems. [...] ·

Jun 17, 2026

[](

--

[](

[](

Listen

Share

JSON schema validation is a key part of reliable LLM function calling because it defines exactly what a function is allowed to receive and return. It sets the structure, data types, required fields, accepted values, and formatting rules before any function is executed. This gives the AI model and the system a clear contract, reducing malformed requests and preventing avoidable runtime errors.

Press enter or click to view image in full size

Image 3

JSON schema validation gives the AI model a clear contract. Source / Syncfusion Blogs

-----

### Source [9]: https://arxiv.org/html/2502.00032v1

Query: advanced patterns function calling LLM schema design validation

Answer: Querying Databases with Function Calling

Tool use is one of the most promising opportunities to improve the capabilities of LLMs. There are two common design patterns for interfacing tool use in Compound AI Systems: Function Calling and Flow Engineering . Visualized in Figure 4, Function Calling entails equipping the LLM with a set of functions described in the prompt. The LLM inference is then orchestrated in a function calling loop. At each step, the LLM either chooses to complete the response, or call one or multiple functions and wait for their respective responses to continue the next iteration of the loop. Contrastively, Flow Engineering describes a pre-determined flow of inferences and external tools calls. This abstraction helps clarify how tools are interfaced to LLMs. However, there is a significant overlap and this is [...] with a searchable text property and three additional properties, one numeric, one textual, and one boolean, to enable comprehensive testing of different query patterns. This structured approach allows us to systematically assess how well LLMs can interpret database schemas and translate natural language requests into appropriate database operations. Given this dataset of schemas, we then create a comprehensive test dataset of queries covering all combinations of query operators defined in the tool schema. These capabilities include search queries for finding relevant results based on relevance ranking algorithms, property filters for matching on integer, text, and boolean fields, aggregations for computing statistics over integer, text, and boolean properties, and grouping operations to

-----

### Source [10]: https://www.thrivewithai.live/blog/function-calling-production-patterns

Query: advanced patterns function calling LLM schema design validation

Answer: Function Calling in Production: Patterns and Pitfalls | Thrive With AI

Thrive With AI - Best AI ML Course 2026 for Professionals
Function Calling in Production: Patterns and Pitfalls

# Function Calling in Production: Patterns and Pitfalls

Turning LLMs into action-takers. Covers function design, error handling, security, validation, and building reliable tool-using AI systems.

Debasish Maji

## From Chat to Action

LLMs that only generate text are limited. Function calling transforms them into actors that can do things.

Search databases. Send emails. Update records. Book appointments. Function calling bridges the gap between AI understanding and real-world action. But with great power comes great complexity.

## Function Calling Fundamentals

### How It Works [...] ### Dynamic Functions

| Approach | Description | Trade-off |
 --- 
| Static registry | Fixed functions | Simple, limited |
| Dynamic loading | Load at runtime | Flexible, complex |
| User-defined | User creates functions | Powerful, risky |

### Multi-Step Reasoning

| Step | LLM Action | System Action |
 --- 
| 1 | Identify goal | Provide functions |
| 2 | Plan steps | Validate plan |
| 3 | Execute step | Run function |
| 4 | Evaluate result | Return result |
| 5 | Continue or finish | Loop or complete |

## Key Takeaways

Function calling transforms LLMs from advisors to actors. Build the bridge carefully, with guardrails and observability, and you will unlock powerful capabilities.

### Found this helpful?

Share it with others who might benefit

## Related articles

-----

