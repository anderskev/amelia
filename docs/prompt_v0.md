# Amelia

## Problem

I am a software engineer who manages multiple ai agent workflows in parallel and I need a user interface where I can manage, monitor, debug and control these workflows. There should be a web application and a command line application, both sharing a common backend.

## Frontend Web

- use "A sidebar that collapses to icons" from https://ui.shadcn.com/blocks/sidebar#sidebar-07
- sidebar header should just contain "Amelia" logo text Momo Trust Display 40px
- sidebar groups should correspond to phases: observe, orient, design, acta
- additional sidebar group: configuration

### Frontend Web Tech Stack

- react router v7, framework mode, single-page application
- shadcn/ui following theme in @docs/global.css
- ai-elements for all llm chat ui https://ai-sdk.dev/elements
- vite

### Observe

- collapsible menu items: Local RAG, Remote Sources
- Local RAG
  - Upload
  - Documents
  - Memories
- Remote Sources
  - Web Scraper (coming soon)
  - Scheduled Jobs (coming soon)

#### Local RAG - Upload

- accepts markdown, pdf, txt
- uses shadcn Input https://ui.shadcn.com/docs/components/input
- uses shadcn Progress https://ui.shadcn.com/docs/components/progress

#### Local RAG - Documents

- show documents currently in RAG database, use Data Table https://ui.shadcn.com/docs/components/data-table
- can filter by filename, 
- can sort by filename, created, size

#### Local RAG - Memories

- show ???

### Orient

- collapsible menu items: Chat, Prioritize, Inform
- Chat
  - New Conversation
  - Old Conversation 1
  - Old Conversation 2
  - ...
  - Conversation History
- Priotitize
  - Coming Soon
- Inform
  - Documents
  - Memories
  - Remote Sources

#### Chat - New/Existing Conversation

- Support blank/new state or loading historic chat
- Should use ai-elements components, example: https://ai-sdk.dev/elements/examples/chatbot
- should support reasoning: https://ai-sdk.dev/elements/components/reasoning
- should use shimmer: https://ai-sdk.dev/elements/components/shimmer
- can upload markdown or text files to chat
- should show current context information using https://ai-sdk.dev/elements/components/context
- agent messages should have action buttons to: retry, copy, add to long term memory
- agent messages should support markdown rendering: https://ai-sdk.dev/elements/components/message

#### Chat - Conversation History

- show conversation title, context window remaining (if available), cost (if available) date and time of last message in Data Table https://ui.shadcn.com/docs/components/data-table
- we can navigate to an old conversation from this view

### Decide

- empty for now "coming soon"
Based on your orientation, weigh the possible courses of action and select the one you believe is best.
Be prepared to change your decision if new information becomes available through the loop. 

### Act

- empty for now "coming soon"

### Configuration

- 2 menu items, not collapsible: Monitoring, Settings

#### Monitoring

- show current size of RAG database
- show graphs of token usage by hour,day, week, month: https://ui.shadcn.com/charts/area#charts
- show all time token usage
- health checks for backend

#### Settings

- username
- how long to retain chat history in db
- RAG document folder path
- openrouter api key
- chat mode (local or cloud)
- local chat agent (claude code via agent client protocol only option for now)
- cloud chat model (default to )

## Frontend Command Line

- all functionality of frontend web EXCEPT chat

### Frontend Command Line Stack

- ink https://github.com/vadimdemedes/ink

## Backend API

### Backend Tech Stack
- astral uv
- python >= 3.12
- fastapi >= 0.121.1
- postres >= with pgvector
- rich >= 14.1
- pydantic AI https://ai.pydantic.dev/
- langgraph >= 1.0.2 https://docs.langchain.com/oss/python/langgraph/overview
- langchain >= 1.0.2
- docling >= 2.61.1 https://docling-project.github.io/docling/reference/document_converter/
- agent client protocol https://github.com/agentclientprotocol/python-sdk

### Features

#### Chat
- can stream messages to openrouter using langchain_openai python library
- uses agent client protocol to interact with claude code running locally https://github.com/zed-industries/claude-code-acp
- chats persisted based on configuration

#### Local RAG


## General Tech Principles

- use structred logging
- use Test Driven Development
- don't pin dependencies unless absolutely necessary, use >=
- entire stack (frontend and backend) should be runnable via docker-compose command
- we do not need performance monitoring beyond basic healthchecks

* kick off claude code agents locally to perform workflows for writing technical design docs, discovery docs, planning docs, bug fixing, testing, code implementation. We will have many different agents with different system prompts representing different parts of the software development lifecycle, including product management functions
* the ui should show realtime updates from running agents such as the work they are doing, summary of what is done so far, what is upcoming
* the ui should show how different agents are ordered in a workflow
* the backend which powers the ui will also control orchestration of the agents, it will run locally and will be in python 3.12+
* the backend should provide RAG functionality to local claude code. We should be able to upload multiple forms of documents: markdown, html, pdf
* the backend should also support the ability to scrape a website and add its content to the RAG database
* we can use either ollama local embeddings or openrouter via openai/text-embedding-3-small model
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