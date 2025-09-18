# AI Product Manager Capability Blueprint

## Scope
End-to-end product management from discovery to delivery and iteration.

## Core Domains
- **Market & User Research**
- **Product Strategy & Goals**
- **Planning & Prioritization**
- **Execution & Delivery**
- **Stakeholder Communication**
- **Evaluation & Learning**

## Inputs
- **External**: Web/news, app reviews, social signals, competitor sites, GitHub issues, ticketing systems
- **Internal**: Product, features, metrics, objectives, sprints, historical performance

## Outputs
- **Artifacts**: PRDs, specs, roadmaps, sprint plans, status reports, decision logs
- **Decisions**: Priorities, resourcing, milestones, go/no-go, scope cuts
- **Insights**: Trend synthesis, user themes, risk flags, metric movements

## Success Metrics
- **Delivery**: Planned vs. actual velocity; roadmap predictability; cycle time
- **Outcome**: Activation, retention, feature adoption, NPS, revenue lift
- **Quality**: Defect rate, incident frequency, support contact rate
- **Efficiency**: Time-to-brief/PRD, research synthesis time, decision latency

## Autonomy Loop
1. **Observe**: Collect research, product state, and metric signals
2. **Orient**: Synthesize, compare against strategy and constraints
3. **Decide**: Propose/choose priorities, objectives, plans
4. **Act**: Generate artifacts, create sprint plans, communicate updates
5. **Learn**: Evaluate outcomes, update strategy and future plans

## Key Capabilities
- **Research**: Competitor tracking, trend detection, sentiment & theme analysis
- **Strategy**: Vision, objectives (OKRs), metrics, constraints
- **Prioritization**: RICE, WSJF, custom value/effort models, scenarios
- **Planning**: Capacity-aware release planning, schedule generation
- **Communication**: Executive summaries, PRDs, status—templated, explainable
- **Evaluation**: Hypotheses, A/B test tracking, retrospective insights
- **LLM CoT**: Structured prompting, tool-augmented reasoning, critique loops

## Safety & Controls
- **Human-in-the-loop**: Approval for material changes
- **Guardrails**: Policy checks, PII redaction, source traceability
- **Audit**: Decision logs with rationale, inputs, and alternatives

## Architecture Overview
- **Data Layer**: SQLite via SQLModel; repositories per entity; event log
- **AI Layer**: Gemini for research synthesis & artifact generation
- **Orchestration**: Agent loop (scheduled); tasks; rule checks
- **Interface**: CLI now; Streamlit dashboard later

## Near-Term Roadmap
1. Persistence layer (SQLite + repositories)
2. Communication module (PRD/status templates)
3. Prioritization frameworks (RICE, WSJF)
4. Streamlit UI dashboard
5. Cadence agent (weekly planning + retros)
6. Data connectors (news, reviews, GitHub, tickets)
7. Evaluation framework
8. Logging/config & deployment
