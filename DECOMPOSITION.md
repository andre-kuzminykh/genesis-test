# Product Decomposition Structure

## Cascade Flow

```
Product
└── Features (5-7 per product)
    └── Roles / Actors (2-5 per feature)
        └── User Stories (3-5 per role)
            └── User Flows (1-3 per story, with Mermaid sequence diagrams)
                └── Use Cases (2-4 per story, Given/When/Then)
                    └── Requirements (functional + non-functional per use case)
```

## Wizard Flow

1. **Product** — name + description → GPT summary → review/edit → Далее
2. **Features** — generated as TEXT list → review/edit text/voice → Далее (saves to backend)
3. **For EACH feature:**
   - **Roles (Actors)** — generated as TEXT → review/edit → Далее (saves actors + feature-actor links)
   - **For EACH role:**
     - **User Stories** — generated from role's perspective → review/edit → Далее
     - **For EACH story:**
       - **User Flows** — generated with Mermaid sequenceDiagram → review/edit → Далее
       - **Use Cases** — Given/When/Then format derived from flows → review/edit → Далее
       - **For EACH use case:**
         - **Requirements** — functional + non-functional → review/edit → Далее
       - → next story
     - → next role
   - → next feature
4. **Done** — all features shown as paginated buttons

## Entity Schemas

### Feature
- `name` — feature name
- `description` — one-sentence description

### Role / Actor
- `name` — role name (e.g. "End User", "Admin")
- `description` — who this role is
- `role_type` — end_user | admin | system | external

### User Story
- `title` — short title
- `want` — what the user wants (from role perspective)
- `benefit` — why they want it

### User Flow
- `title` — flow name
- `flow_type` — primary | alternative | exception
- `description` — step-by-step description
- `mermaid_source` — Mermaid sequenceDiagram code

Example mermaid:
```
sequenceDiagram
    User->>Frontend: Click login
    Frontend->>API: POST /auth/login
    API->>DB: Verify credentials
    DB-->>API: User data
    API-->>Frontend: JWT token
    Frontend-->>User: Dashboard
```

### Use Case (Given/When/Then)
- `title` — use case name
- `goal` — what the use case achieves
- `given_text` — preconditions
- `when_text` — action/trigger
- `then_text` — expected outcome

### Requirement
- `title` — requirement name
- `text` — detailed description
- `requirement_type` — functional | non-functional
- `priority` — high | medium | low

## Backend API Endpoints

| Entity | Create | Get All | Get By ID | Approve |
|--------|--------|---------|-----------|---------|
| Products | POST /products | GET /products | GET /products/:id | POST /products/:id/approve |
| Features | POST /features | GET /features | GET /features/:id | POST /features/:id/approve |
| Actors | POST /actors | GET /actors | GET /actors/:id | POST /actors/:id/approve |
| Feature-Actor Links | POST /feature-actor-links | GET /feature-actor-links | — | — |
| Stories | POST /stories | GET /stories | GET /stories/:id | POST /stories/:id/approve |
| Flows | POST /flows | GET /flows | GET /flows/:id | POST /flows/:id/approve |
| Use Cases | POST /use-cases | GET /use-cases | GET /use-cases/:id | — |
| Requirements | POST /requirements | GET /requirements | GET /requirements/:id | POST /requirements/:id/approve |

## UX Rules

- ONE bot message, always edited in-place
- User messages deleted instantly
- TEXT lists first — only saved to buttons after "Далее"
- Edit via text or voice at every review step
- Pagination: always 3 buttons [◀️] [page/total] [▶️], max 5 items per page
- No "saved" confirmation messages — each Далее saves silently and drills deeper
- Buttons appear when user returns from main menu to see saved state
