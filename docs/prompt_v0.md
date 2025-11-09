I want to make an application named Amelia which can act as an orchestration command center for my LLM software development workflow. Here are some features I have in mind:
* web ui using shadcn/tailwindcss/radix ui, runs locally, client-side only NOT server-side rendered, react router v7 framework mode
* terminal ui, considering ink https://github.com/vadimdemedes/ink but open to suggestions. ideally we can share some code with web ui
* both ui have the same capabilities, and run locally
* kick off claude code agents locally to perform workflows for writing technical design docs, discovery docs, planning docs, bug fixing, testing, code implementation. We will have many different agents with different system prompts representing different parts of the software development lifecycle, including product management functions
* the ui should show realtime updates from running agents such as the work they are doing, summary of what is done so far, what is upcoming
* the ui should show how different agents are ordered in a workflow
* the backend which powers the ui will also control orchestration of the agents, it will run locally and will be in python 3.12+
* the backend should provide RAG functionality to local claude code. We should be able to upload multiple forms of documents: markdown, html, pdf
* the backend should also support the ability to scrape a website and add its content to the RAG database
* the backend should use langgraph https://docs.langchain.com/oss/python/langgraph/overview
* the backend should use docling https://docling-project.github.io/docling/reference/document_converter/
* the backend should use pydantic AI https://ai.pydantic.dev/
* the backend should use postrgresql with pgvector
* the backend should use fastapi
* we can use either ollama local embeddings or openrouter via openai/text-embedding-3-small model
* the ui should have a chat interface which uses the AI SDK ai-elements library: https://ai-sdk.dev/elements
* the chat should be configurable to use either a local instance of claude, or stream messages from openrouter
* the chat should replicate features of popular llm chat interfaces such as showing a "thinking" indicator, streaming chunks as they arrive, have copy buttons, being able to display markdown etc
* strongly favor using pre-built components from ai-elements, shadcn or radix ui, only create custom components as a last resort
* use shadcn theme from global.css

in addition, we have another need for this application which is providing context to claude code. The core, first workflow we need to support is:
* download multiple documents from google docs
* use web ui to upload to RAG
* use web ui to kick off claude code agents to perform discovery for a feature mentioned in the uploaded documents
* the agents will use the documents in RAG database, as well as local code repositories to develop comprehensive technical design documents in markdown
* while the agents work, you should see progress and summary updates in the web ui
* once the planning phase is complete, we should be able to use the web ui to kick off agents for the software development lifecycle
* the agents should plan out an implementation of the design from the planning phase documents, and show progress upgrades in the web ui
* the web ui can then be used to trigger code implementation claude code agents, and testing/validation agents
* the web ui can also be used for git worktree management

we do not need observability or monitoring or user accounts. this will be an open source project which is run by software engineers locally on their machine. We also don't strictly need realtime communication, a small delay between agent and ui is fine. Generally favor simple solutions over complex unless otherwise specified. Generate a comprehensive technical design document