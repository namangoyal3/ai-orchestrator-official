# AI Orchestrator Official 🚀

A universal infrastructure layer for AI orchestration. This system serves as a gateway to multiple LLMs, specialized agents, and a marketplace of tools (MCP, built-in, and community-driven).

## 🌟 Key Features

- **Multi-LLM Routing**: Automatically routes tasks to the optimal provider (Claude, GPT, Gemini).
- **Agent Marketplace**: Access to dozens of pre-configured agents for research, coding, documentation, and data analysis.
- **Tool Orchestration**: Seamless execution of MCP (Model Context Protocol) servers and built-in tools.
- **Real-time Analytics**: Built-in dashboard to monitor request volume, success rates, and token costs.
- **Enterprise-ready**: Scalable FastAPI backend with SQLAlchemy/PostgreSQL support.

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Anthropic/OpenAI/Google SDKs.
- **Frontend**: Next.js (App Router), Tailwind CSS, Framer Motion for animations.
- **Deployment**: Optimized for Railway (Backend) and Vercel (Frontend).

## 🚀 Deployment

The system is designed for one-click deployment.

### Backend (Railway)
1. Navigate to `backend/`
2. Run `railway up`
3. Set your `ANTHROPIC_API_KEY` and `DATABASE_URL` in Railway Variables.

### Frontend (Vercel)
1. Navigate to `frontend/`
2. Run `vercel --prod`
3. Set `NEXT_PUBLIC_API_URL` to your Railway URL.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
