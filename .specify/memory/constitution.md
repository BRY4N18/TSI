<!--
SYNC IMPACT REPORT
Version: 1.3.0 → 2.0.0 (structural split: governance vs. implementation docs)
Ratification date: 2026-06-25
MAJOR bump justification: sections 10-18 (Technology Stack, Project Structure,
  Architectural Patterns, Code Conventions, Testing Rules, REST API Standards,
  Project Constraints, Ontology/Glossary, Interface Design System) were removed
  from this document — not because they stopped mattering, but because they are
  implementation detail, not governance. Removing a section that previously had
  normative weight is a MAJOR change per this document's own versioning rule,
  even though no principle's *meaning* changed.
Where the removed content now lives:
  - Technology Stack (10) + Pinot topology (10.1) + Data infrastructure (16.1)
    → .specify/docs/infra/infrastructure.md
  - Project Structure (11) → .specify/docs/architecture/project-structure.md
  - Architectural Patterns (12) → .specify/docs/architecture/architectural-patterns.md
  - Code Conventions (13) → .specify/docs/architecture/conventions-code.md
  - Testing Rules (14) → .specify/docs/architecture/testing.md
  - REST API Standards (15) → .specify/docs/architecture/api-standards.md
  - System critical path (16.2) → kept here, see Additional Constraints
  - System actors (16.3) → .specify/docs/actors.md
  - Sensitive data (16.4) → removed as duplicate; already covered by Principle V
  - Individual project (16.5) → folded into Purpose, one line
  - Ontology / Glossary (17) → .specify/docs/glossary.md
  - Interface Design System (18) → .specify/docs/design/design-system.md
Rationale: this constitution now contains only what arbitrates difficult
  decisions (the 9 ISO/IEC 25010:2023 characteristics, the tie-breaker
  mechanism, validation metrics, governance). Anything that changes for
  reasons unrelated to project values (a linter version, a color hex code,
  a coverage percentage) no longer forces a constitution re-ratification.
Dependent templates: module-map.md, infraestructura.md, actores.md,
  glosario.md already exist and absorb the removed content — no further
  action needed on them as a result of this change.
Next: see Annex A for sub-characteristic correspondence

2026-06-28 PATCH 2.0.0→2.0.1: corrected all path references from `docs/arquitectura/`
  and `docs/` to the actual locations under `.specify/docs/`. No normative change.
-->

# Constitution of Trafico Seguro Integral

## Purpose of this document

This constitution governs all specification, planning, and implementation work for the
**Road Emergency Management System** of Trafico Seguro Integral (TSI), under the
Spec-Driven Development (Spec Kit) workflow. It has authority over any individual spec or plan:
no `/plan` or `/tasks` may contradict this constitution without an explicit exception
justification, documented and approved according to the process described in the Governance section.

The system manages the traffic accident lifecycle (registration, emergency unit dispatch,
data intelligence generation) for emergency operators, insurance companies,
municipalities, and Smart City platforms. By its nature, the system directly affects the
physical safety of real people and handles sensitive data (location, identity of
accident victims, potentially health-related data). This critical nature
is why ISO/IEC 25010:2023 is adopted as the mandatory normative framework, rather than
a generic quality checklist.

This is an individual project developed by a single person (Bryan Humberto Lombeida
Escaleras). Every technical decision favors solutions the sole responsible person can
maintain, debug, and scale without dependence on undocumented tacit knowledge — this is
why Maintainability holds default priority among the characteristics below.

**This document covers only governance: what every spec/plan/task must justify, and how
conflicts between quality characteristics are resolved.** Technology stack, project
structure, code conventions, testing thresholds, API format, actors, glossary, and visual
design system are implementation detail and live in `.specify/docs/` —
see Sync Impact Report above for exact locations. Reference those documents directly when
writing a `/plan`; do not duplicate their content here.

## Golden Rule

**Every spec, plan, or implementation task must explicitly justify how it complies with the
9 main software product quality characteristics defined in ISO/IEC
25010:2023 (SQuaRE — November 2023 edition):**

1. Functional Suitability
2. Reliability
3. Performance Efficiency
4. Interaction Capability — replaces "Usability" in the 2023 edition
5. Security
6. Compatibility
7. Maintainability
8. Flexibility — replaces "Portability" in the 2023 edition
9. Safety — new characteristic in the 2023 edition

Merely mentioning them is not enough: each characteristic relevant to the functionality under specification
must have a traceable justification (see "Validation Metric" below). If a
characteristic does not apply to a specific functionality, the spec must explicitly say
"Not applicable" and why, rather than silently omitting it.

## Core Principles

### I. Functional Suitability as Contract

Every specified functionality must verifiably declare what business need
it satisfies (functional completeness), that it produces correct results within the required
precision (functional correctness), and that it is appropriate for the operational context of road
emergencies (functional appropriateness). Specifications of features "just because" without
traceability to a strategic, tactical, or operational objective (OE/OT/OP) or to a documented
use case (UC) are not accepted.

**Why it is non-negotiable:** an emergency dispatch system with ambiguous or
incomplete functionality is not a minor quality defect — it is a direct risk to the lives of
people involved in an accident.

### II. Operational Reliability (Always-On)

The system must specify and verify maturity (fault tolerance during normal operation),
availability, fault tolerance, and recoverability for every
component that participates in the chain: accident registration → unit assignment → dispatch →
confirmation. Any new functionality in this critical chain must specify its behavior
under failure (degradation, retries, failover) before moving to `/plan`.

**Why it is non-negotiable:** a system crash during ambulance dispatch is not
a bug — it is an unattended medical emergency.

### III. Real-Time Performance Efficiency

Every flow that touches the emergency dispatch critical path must declare measurable
temporal behavior (maximum latency), resource utilization, and capacity (maximum supported
volume) in its acceptance criteria. Data intelligence and analytical reporting flows
(non-time-critical) may have looser thresholds, but must still declare them.

**Why it is non-negotiable:** in emergency management, degraded performance translates
directly into minutes lost before help arrives.

### IV. Inclusive Interaction Capability

Every interface aimed at emergency operators, field technicians, or 24/7 support must
prioritize appropriateness recognizability, ease of
learning, operability under pressure, user error protection, interaction
aesthetics, accessibility/inclusivity, and self-descriptiveness. For critical operational
roles (Operator, Field Technician), ease of learning and user error prevention
take priority over visual aesthetics.

**Why it is non-negotiable:** an operator working under pressure in a real accident cannot
afford a confusing or ambiguous interface.

### V. Information Security by Design

Every piece of data that passes through the system —especially geolocation data, identity of
people involved in accidents, and data shared with insurance companies or municipalities via
API— must explicitly specify: confidentiality (encryption in transit and at rest,
role-based access control), integrity (verification against tampering), non-repudiation,
accountability (traceability of who accessed what), authenticity of
sources, and attack resistance. No specification for an API endpoint, report
export, or third-party integration (insurers, Smart Cities, partners) may advance to
`/plan` without addressing access control and sensitive data handling.

**Why it is non-negotiable:** the system's data links location and potential health
data of real people; a security breach is not just a technical incident — it is an
exposure of sensitive information about accident victims.

### VI. API-First Compatibility and Interoperability

Given that TSI's business model depends on API integrations with insurance companies,
municipalities, and Smart City platforms (coexistence and interoperability), every externally
exposed functionality must be specified with a versioned API contract, documentation, and
backward compatibility tests before any change that would break existing integrations.

**Why it is non-negotiable:** breaking an active integration with an insurance company not only affects
recurring revenue — it disrupts the information flow that insurer uses to process
real claims.

### VII. Maintainability as Structural Priority

Maintainability (modularity, reusability, analyzability, modifiability,
testability) is, together with Functional Suitability, one of the two characteristics that
**win by default** in any trade-off conflict (see Tie-Breaker Mechanism). Every
technical plan must declare how the proposed solution keeps coupled complexity low and
testability high, even if that means giving up a marginal performance optimization
or a "faster to implement but harder to maintain" solution.

**Why it is non-negotiable:** this is an individual project (no backup team);
unmaintainable code today is inoperable functionality tomorrow when the person responsible
does not remember the original context or needs to scale quickly for a new city or integration.

### VIII. Multi-Region Flexibility and Scalability

Every architecture decision must declare how it adapts to new cities/regions
(adaptability), how it installs/deploys (installability), and how it scales without degrading
service (scalability) or requiring replacement of critical components (replaceability). This
applies directly to the operational goal of onboarding new regions without loss of service
quality.

**Why it is non-negotiable:** TSI's business model explicitly depends on scaling to
new markets without degrading service; a rigid architecture blocks the very growth
that sustains the project.

### IX. Physical Safety Above All

This is the characteristic that can **override the default tie-breaker** (see Tie-Breaker
Mechanism). Every functionality that influences emergency unit assignment or dispatch,
accident severity classification, or any decision where a
system error could delay or divert attention from a real victim, must specify:
operational constraints, hazard identification, fail-safe
behavior, hazard warning, and safe integration mechanisms with
external units (ambulances, tow trucks, police).

**Why it is non-negotiable:** it is the system's very reason for existence. No business goal,
delivery deadline, or cost saving justifies a decision that increases the physical risk
of a person waiting for an ambulance.

## Tie-Breaker Mechanism

When two or more ISO/IEC 25010:2023 characteristics come into direct conflict in the same
design decision (typical example: Information Security slows down Performance
Efficiency; or Multi-Region Flexibility adds complexity that reduces Maintainability), the
following priority order applies:

1. **First:** if the decision affects the **Safety** of real people in the
   context of an active emergency (e.g., dispatch, severity classification, unit
   geolocation) — **Safety has absolute priority** over any other characteristic,
   including Maintainability and Functional Suitability.
2. **If Safety is not at stake:** **Maintainability** and **Functional Suitability** have
   default priority over the remaining characteristics.
3. **Domain exception:** if the specific case involves sensitive identity or health
   data in transit or at rest (e.g., report export to insurers, photographic accident
   evidence storage), **Information Security** may take priority over
   Maintainability — but never over Safety.

**Every plan that invokes this mechanism must explicitly document:**

- Which characteristics were in conflict.
- Which one was prioritized and under which rule of this mechanism.
- The specific trade-off accepted (what was sacrificed and its expected impact).

A plan that does not document the trade-off when an evident conflict exists is considered
incomplete and must be rejected during review.

## Validation Metric (mandatory per user story)

Each specified user story or use case must include **at least one measurable
acceptance criterion** based on an ISO/IEC 25010:2023 sub-characteristic. The concrete
thresholds currently in force (latency targets, coverage percentages, uptime SLAs, etc.)
live in `.specify/docs/architecture/testing.md` and the relevant spec's own acceptance criteria —
this section only fixes the _kind_ of sub-characteristic each example illustrates, not the
specific number, since the number is calibration and may legitimately change project to
project without that being a constitutional matter:

| Characteristic         | Sub-characteristic    | Example measurable criterion                                          |
| ---------------------- | --------------------- | --------------------------------------------------------------------- |
| Performance Efficiency | Temporal behavior     | Dispatch latency ≤ 100ms (p95)                                        |
| Reliability            | Availability          | Uptime ≥ 99.99% monthly                                               |
| Maintainability        | Testability           | Automated test coverage > 80%                                         |
| Security               | Confidentiality       | 100% of geolocation data encrypted in transit and at rest             |
| Safety                 | Fail-safe behavior    | On dispatch algorithm failure, manual reassignment available in ≤ 30s |
| Interaction Capability | User error prevention | Accident registration error rate < 1%                                 |
| Flexibility            | Scalability           | New city operational in ≤ 30 days without degrading existing SLA      |
| Compatibility          | Interoperability      | Versioned API contracts without unannounced breaking changes          |

A spec without at least one measurable criterion of this type cannot advance to `/plan`.

## Additional Constraints

- **Mandatory traceability:** every specification must be linked to a strategic
  (OE), tactical (OT), or operational (OP) objective, or to a use case
  (UC) already documented in the project's Balanced Scorecard, or explicitly declare
  that it introduces a new one and why.
- **Critical path:** the chain accident registration → data validation → unit assignment →
  dispatch confirmation → tracking is the system's critical path. Any change affecting
  this chain requires explicit justification of Safety impact (Principle IX) and
  Reliability impact (Principle II) before implementation.
- **Sensitive data:** no geolocation data, identity of accident victims,
  or photographic evidence may be exposed via API or report without role-based access control
  and access audit logging (this operationalizes Principle V for this specific data category).

## Development Flow (Spec Kit)

1. `/constitution` — this document. Any future changes follow the Governance process.
2. `/specify` — every new specification must explicitly declare which ISO/IEC 25010:2023
   characteristics apply and which do not, with justification.
3. `/plan` — every plan must pass the Tie-Breaker Mechanism check if a conflict exists between
   characteristics; if there is no conflict, it must likewise declare it ("no conflicts
   identified"). Plans should reference `.specify/docs/architecture/` for stack, patterns, and
   conventions rather than re-deciding them.
4. `/tasks` — each task inherited from a plan that touches the dispatch critical path must explicitly
   include its measurable acceptance criterion (see Validation Metric).
5. `/implement` — no implementation is considered complete without verification that it meets
   the measurable criteria declared in its originating user story.

## Governance

- This constitution prevails over any individual spec, plan, or task. In case of
  contradiction, the constitution wins, except for a documented and explicitly approved exception.
- **Exceptions:** a principle may only be contradicted if the corresponding plan documents
  the reason, the accepted risk, and a review date or condition. Exceptions related
  to Principle IX (Safety) require reinforced justification and cannot remain open
  indefinitely.
- **Versioning:** this constitution uses semantic versioning (MAJOR.MINOR.PATCH):
  - **MAJOR:** removal or incompatible redefinition of an existing principle.
  - **MINOR:** addition of a new principle or material constraint, or substantial expansion of
    existing guidance.
  - **PATCH:** clarifications, wording corrections, or adjustments that do not change the
    normative meaning.
- **Review:** any modification to this document must include a Sync Impact Report (like the
  comment at the beginning of this file) detailing what changed and which dependent
  templates or specs must be reviewed accordingly.
- Since this is an individual project, the responsible person (Bryan Humberto Lombeida Escaleras)
  is the approval authority for any change or exception to this constitution.

## Annex A — ISO/IEC 25010:2023 Correspondence with the 2011 Edition

To avoid confusion when consulting reference material prior to November 2023:

| 2023 Edition (current, used in this constitution)                                                     | 2011 Edition (obsolete)                           |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Interaction Capability                                                                                | Usability                                         |
| Flexibility                                                                                           | Portability                                       |
| Safety                                                                                                | — (did not exist as a main characteristic)        |
| Functional Suitability, Reliability, Performance Efficiency, Security, Compatibility, Maintainability | Unchanged name, with expanded sub-characteristics |

**Version**: 2.0.1 | **Ratified**: 2026-06-21 | **Last modified**: 2026-06-28
