# Gaji (가지): Branch All of Story

<div align="center">

**🌿 Explore infinite timelines. Where every story branches. 🌿**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Java](https://img.shields.io/badge/Java-17+-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Vue](https://img.shields.io/badge/Vue-3.x-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.x-336791.svg)](https://www.postgresql.org/)

</div>

---

## 📖 What is Gaji?

**Gaji** (가지, Korean for "branch") is a revolutionary platform that brings **"What If?"** storytelling to life. Inspired by Marvel's What If...? and powered by AI, Gaji enables readers to explore alternative timelines where beloved characters face different circumstances, make different choices, or exist in entirely different settings.

Unlike traditional book discussion platforms, Gaji doesn't just let you talk _about_ books—it lets you **fork reality itself** and explore infinite story possibilities.

### 🌟 Core Concept

```
📚 Classic Story
    ├─ 🔀 What if Hermione was sorted into Slytherin?
    │   ├─ 💬 Conversation: How did it affect her friendships?
    │   └─ 💬 Conversation: What about her rivalry with Harry?
    │
    ├─ 🔀 What if Gatsby never met Daisy?
    │   ├─ 💬 Conversation: Would he still pursue wealth?
    │   └─ 🔀 Meta-fork: What if he became a tech entrepreneur?
    │
    └─ 🔀 What if Pride & Prejudice happened in 2024 Seoul?
        └─ 💬 Conversation: How does Darcy's pride translate to K-drama?
```

### 🎯 Key Features

- **🔀 Scenario Forking**: Create "What If" scenarios with three types:

  - **Character Changes**: "What if Hermione was in Slytherin?"
  - **Event Alterations**: "What if Gatsby never met Daisy?"
  - **Setting Modifications**: "What if Pride & Prejudice was set in 2024 Seoul?"

- **💬 AI Character Conversations**: Talk to characters adapted to alternate timelines
- **🌳 Tree Visualization**: Explore how scenarios branch into infinite variations
- **👥 Social Discovery**: Share viral timelines and fork others' creative scenarios
- **📊 Community-Driven**: Like, follow, and collaborate on story explorations

---

## 🏗️ Architecture Overview

Gaji uses a **microservices architecture (Pattern B: API Gateway)** with clear separation of concerns:

```mermaid
graph TD
    A[Vue.js Frontend<br/>Single API Client] -->|HTTPS /api/*| B[Spring Boot API Gateway<br/>Port 8080]
    B -->|/api/ai/* Proxy| C[FastAPI AI Backend<br/>Port 8000 Internal]
    B -->|JPA CRUD| D[PostgreSQL 15.x<br/>Metadata Only]
    C -->|Semantic Search| E[VectorDB ChromaDB/Pinecone<br/>Content + Embeddings]
    C -->|AI Generation| F[Gemini 2.5 Flash<br/>Text + Embeddings]

    style A fill:#42b883,stroke:#333,stroke-width:2px
    style B fill:#FFD54F,stroke:#333,stroke-width:3px
    style C fill:#3572A5,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style D fill:#336791,stroke:#333,stroke-width:2px
    style E fill:#FF6347,stroke:#333,stroke-width:2px
    style F fill:#4285F4,stroke:#333,stroke-width:2px
```

**Architecture Pattern**: **Pattern B (API Gateway)** ✅
- Frontend → Spring Boot ONLY (single entry point)
- Spring Boot → FastAPI (internal proxy, not externally exposed)
- Enhanced Security: FastAPI/Gemini API keys protected from external access
- Cost Savings: $700/year saved on SSL/domains
- Performance: +50ms overhead is negligible (1%) on 5000ms AI operations

### Technology Stack

| Layer            | Technology                           | Purpose                                        |
| ---------------- | ------------------------------------ | ---------------------------------------------- |
| **Frontend**     | Vue 3, PrimeVue, PandaCSS, Pinia     | Modern SPA with component-based UI             |
| **API Gateway**  | Java 17+, Spring Boot 3.x (Port 8080) | **Single entry point**, AI proxy, business logic |
| **AI Backend**   | Python 3.11+, FastAPI (Port 8000)    | **Internal only**, RAG, VectorDB, Gemini API   |
| **Metadata DB**  | PostgreSQL 15.x (13 tables)          | Users, novels, scenarios, conversations        |
| **Content DB**   | ChromaDB/Pinecone (5 collections)    | Passages, characters, locations, events, themes |
| **AI/ML**        | Gemini 2.5 Flash, Gemini Embedding   | Text generation (768-dim embeddings)           |

**Key Architecture Decisions**:
- ✅ **Pattern B (API Gateway)**: Security, simplicity, centralized logging
- ✅ **Hybrid Database**: PostgreSQL (ACID) + VectorDB (semantic search 10x faster)
- ✅ **SSE Streaming**: Real-time AI responses, 93% fewer network requests
- ✅ **Multirepo Structure**: Independent repositories for each service

**📚 Documentation**:
- [**architecture.md**](./architecture.md) - Complete architecture guide (System Architecture Document)
- [**IMPLEMENTATION_ROADMAP.md**](./docs/IMPLEMENTATION_ROADMAP.md) - Next steps & timeline
- [**BACKEND_OPTIMIZATION.md**](./docs/BACKEND_OPTIMIZATION.md) - 7 performance strategies
- [**DATABASE_STRATEGY.md**](./docs/DATABASE_STRATEGY.md) - Hybrid database design
| **AI/ML**        | Gemini 2.5 Flash, Gemini Embedding   | Text generation (768-dim embeddings)           |
| **Deployment**   | Railway (backend), Vercel (frontend) | Cloud infrastructure                           |

## 📊 Database Schema

Gaji uses a **Hybrid Database Architecture** (PostgreSQL + VectorDB):

### PostgreSQL (13 tables)
- **Metadata**: Users, novels, scenarios, conversations, messages
- **Social**: Follows, likes, memos, forks
- **Features**: ACID transactions, complex JOINs, B-Tree indexing

### VectorDB (5 collections)
- **Content**: Novel passages (chunked 200-500 words)
- **AI Analysis**: Characters, locations, events, themes
- **Search**: Semantic search via 768-dim embeddings (Gemini)
- **Performance**: 10x faster than pgvector on semantic queries

**Why Hybrid?**
- PostgreSQL: Best for relational metadata queries
- VectorDB: Best for semantic "find brave scenes" searches
- **Combined**: Best of both worlds

See [DATABASE_STRATEGY.md](docs/DATABASE_STRATEGY.md) for detailed comparison.

---

## 🎨 User Experience

### Creating a "What If" Scenario

1. **Select Base Story**: Choose from popular books (Harry Potter, Pride & Prejudice, etc.)
2. **Choose Scenario Type**:
   - **Character Change**: Modify a character's properties (house, personality, etc.)
   - **Event Alteration**: Change what happens at a key moment
   - **Setting Modification**: Shift time period or location
3. **Configure Parameters**: Fill in structured templates (no freeform text chaos)
4. **Validate**: AI checks for logical coherence
5. **Publish**: Share with the community

### Exploring Scenarios

- **Browse by Book**: See all "What If" scenarios for your favorite stories
- **Trending Timelines**: Discover viral scenarios gaining rapid forks
- **Fork & Remix**: Create meta-scenarios by branching existing timelines
- **Tree Visualization**: Navigate the multiverse with D3.js-powered graphs

### AI Conversations

**Example Prompt (Auto-generated)**:

```
You are Hermione Granger in an alternate timeline where you were
sorted into Slytherin instead of Gryffindor. You befriended Draco
Malfoy in your first year, developed cunning ambition under Snape's
mentorship, and experienced the complete Harry Potter series from
Slytherin's perspective. Discuss your alternate journey with readers.
```

**User**: "How did being in Slytherin change your relationship with Harry?"

**AI Hermione**: "It was complicated. We were rivals at first—he saw
me as a traitor to 'good' wizards. But in our third year, during the
Sirius Black incident, we realized we were fighting the same battle
from different houses..."

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Java**: Google Java Style Guide
- **Python**: Black + flake8
- **TypeScript/Vue**: ESLint + Prettier

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Inspiration**: Marvel's What If...?, Archive of Our Own (AO3)
- **AI Models**: Local LLM (Llama, Mistral, or similar open-source models), LangChain ecosystem
- **UI Components**: PrimeVue, PandaCSS
- **Community**: BookTok creators, fanfiction writers, literature professors

---

## Team

Meet the team behind Gaji:

<div align="center">

| Member     | GitHub                                       | Role           |
| ---------- | -------------------------------------------- | -------------- |
| **민영재** | [@yeomin4242](https://github.com/yeomin4242) | Core Developer |
| **구서원** | [@swkooo](https://github.com/swkooo)         | Core Developer |

</div>

We're a passionate team of developers building the future of interactive storytelling! 🚀

---

## 📞 Documentation & Resources

### 📂 Core Documentation
- [**architecture.md**](./architecture.md) - System architecture & ADRs
- [**IMPLEMENTATION_ROADMAP.md**](./docs/IMPLEMENTATION_ROADMAP.md) - Next steps & timeline
- [**CLAUDE.md**](./CLAUDE.md) - AI development guide

### 🛠️ Implementation Guides
- [**DEVELOPMENT_SETUP.md**](./docs/DEVELOPMENT_SETUP.md) - Local environment setup
- [**BACKEND_OPTIMIZATION.md**](./docs/BACKEND_OPTIMIZATION.md) - Performance strategies
- [**DATABASE_STRATEGY.md**](./docs/DATABASE_STRATEGY.md) - Hybrid DB design

### 📋 Specifications
- [**PRD.md**](./docs/PRD.md) - Product requirements
- [**ERD.md**](./docs/ERD.md) - Database schema
- [**API_DOCUMENTATION.md**](./docs/API_DOCUMENTATION.md) - API reference
- [**TESTING_STRATEGY.md**](./docs/TESTING_STRATEGY.md) - Testing guidelines
- [**UI_UX_SPECIFICATIONS.md**](./docs/UI_UX_SPECIFICATIONS.md) - Design specs
- [**SECURITY.md**](./docs/SECURITY.md) - Security best practices

### 📖 Epic & Story Details
- [**Epics**](./docs/epics/) - 7 epic specifications
- [**Stories**](./docs/stories/) - 37 user story implementations

---

## Contact & Support

- **Documentation**: [/docs](/docs)
- **Issues**: [GitHub Issues](https://github.com/SideProjectSFY/gajiFE/issues)
- **Email**: Contact via GitHub

---

<div align="center">

**🌿 Let's gaji some timelines! 🌿**

Made with ❤️ by the Gaji team

[Website](https://gaji.app) • [Docs](docs/) • [Blog](https://blog.gaji.app)

</div>
