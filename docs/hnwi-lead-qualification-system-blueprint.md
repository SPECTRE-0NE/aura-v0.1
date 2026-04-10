# Automated HNWI Lead Qualification System (Operational Blueprint)

## A. System overview

This system is a production lead-intelligence pipeline for an estate-focused outbound call centre. It turns raw, incomplete leads into prioritized calling actions with full score explainability.

**What it does end-to-end:**
1. Ingests leads from CRM/forms/CSV/list vendors/manual entry.
2. Cleans and standardizes identity/contact/company fields.
3. De-duplicates and links records into one canonical lead profile.
4. Resolves identity confidence across multiple lawful data sources.
5. Enriches with public and licensed non-sensitive wealth signals.
6. Scores lead quality (wealth capacity + offer fit + decision power) out of 100.
7. Assigns confidence and tier classification.
8. Routes to priority dial queue, standard queue, nurture, or manual review.
9. Logs every input, source, rule, model contribution, and final action for audit.
10. Learns from call and revenue outcomes to continuously recalibrate scoring.

**Design principles:**
- Fast triage (minutes, not days).
- Deterministic + probabilistic hybrid (rules first, models second).
- Explainability by default (no black box-only routing).
- POPIA-aware handling and minimization.
- Human escalation only for uncertainty or high-value exceptions.

---

## B. Workflow

### Step-by-step flow from raw lead to routed outcome

1. **Lead Intake**
   - Receive payload from source connector.
   - Validate schema and required minimum (at least one contact key: phone/email + name or company).
   - Generate `lead_id` and `ingestion_batch_id`.

2. **Normalization**
   - Standardize:
     - Names (`title`, `first`, `middle`, `last`, suffix).
     - Phone (E.164 format).
     - Email (lowercase, alias normalization rules).
     - Address/geography (city/suburb/province/country code).
     - Company entity (strip legal suffixes, canonicalization).

3. **Deduplication & Entity Linking**
   - Exact-match keys: normalized phone, email, tax/business ID (if present).
   - Probabilistic match keys: name+company+geo+title.
   - Merge into canonical `person_entity_id` if confidence threshold met.

4. **Identity Resolution**
   - Run matching graph against existing identities and external records.
   - Compute `identity_confidence` (0–1).
   - If `identity_confidence < low_threshold`, set manual verification queue.

5. **Data Enrichment (Lawful Sources Only)**
   - Pull signals from licensed/public providers:
     - Corporate registries, director/officer records.
     - Professional profile APIs/data partners.
     - News/media databases.
     - Public speaking/board affiliations.
     - Legally accessible property/area indicators.
   - Store each signal with source, timestamp, and confidence.

6. **Lifestyle/Wealth Signal Evaluation**
   - Convert raw enrichment into standardized feature signals:
     - Seniority, ownership, capital access proxies, influence, area quality.
   - Apply reliability weights by source quality and recency.

7. **Scoring**
   - Compute weighted score out of 100.
   - Compute separate dimensions:
     - Wealth capacity score.
     - Offer-fit score.
     - Contactability score.
     - Decision-maker probability.
   - Output overall score + confidence band.

8. **Classification**
   - Map score + confidence + hard rules into Tier 1–5.
   - Apply overrides (e.g., sanctions risk, explicit opt-out, known student, non-decision-maker).

9. **Routing & Action**
   - Tier 1: immediate priority dialer + senior closer script.
   - Tier 2: same-day/next-day dial queue + standard closer.
   - Tier 3: nurture sequence + scheduled callback.
   - Tier 4: analyst/manual review workflow.
   - Tier 5: disqualify with reason code.

10. **Outcome Capture & Learning**
    - Capture call dispositions and revenue outcomes.
    - Feed calibration jobs weekly/monthly.
    - Update feature weights and threshold policies under governance.

---

## C. Architecture

### 1) Ingestion Layer
- **Connectors:** CRM webhook, batch CSV importer, form API, list vendor SFTP/API.
- **Responsibilities:** validation, schema mapping, idempotent ingestion, event publishing.

### 2) Data Standardization Service
- Canonicalization of person/company/contact/location fields.
- Country-aware parsing rules (phone/address/company suffixes).

### 3) Identity Graph Service
- Person/company graph with deterministic + fuzzy matching.
- Maintains `entity_id` links and match confidence.

### 4) Enrichment Orchestrator
- Executes provider adapters with retry/rate limiting.
- Prioritizes high-yield sources first for latency/cost control.

### 5) Feature Store (Lead Signals)
- Stores normalized features used by scorer.
- Versioned feature definitions for reproducibility.

### 6) Scoring Engine
- Rules + weighted scoring + optional calibrated ML model.
- Produces score breakdown and confidence.

### 7) Classification & Routing Engine
- Tier assignment and queue/nurture action triggers.
- Script assignment logic by persona/wealth signal profile.

### 8) Compliance & Audit Service
- Data provenance ledger.
- Explainability trail (why score, why route).
- Consent/opt-out enforcement.

### 9) Ops UI / Agent Console
- Shows score, confidence, top 5 reasons, source links, recommended script.
- Enables manual overrides with mandatory reason code.

### 10) Analytics & Feedback Loop
- Tracks funnel performance by signal and source.
- Monitors false positives/negatives, drift, and ROI per tier.

**Connectivity pattern:** Event-driven (message bus) + transactional DB for canonical records + warehouse for analytics.

---

## D. Data model

### Core tables / objects

1. **`leads_raw`**
   - `raw_lead_id`, `source_system`, `source_record_id`, `payload_json`, `received_at`

2. **`leads_canonical`**
   - `lead_id`, `person_entity_id`, `company_entity_id`, standardized fields, `ingestion_batch_id`, `created_at`

3. **`identities`**
   - `person_entity_id`, candidate attributes, `identity_confidence`, `resolution_status`, `manual_review_flag`

4. **`identity_matches`**
   - `match_id`, `person_entity_id`, `external_record_id`, `source_id`, `match_features_json`, `match_score`, `matched_at`

5. **`enrichment_signals`**
   - `signal_id`, `person_entity_id`, `signal_type`, `signal_value`, `normalized_value`, `source_id`, `source_confidence`, `observed_at`, `expires_at`

6. **`source_registry`**
   - `source_id`, `provider_name`, `source_type` (public/licensed/internal), `license_ref`, `quality_rating`

7. **`feature_snapshots`**
   - `snapshot_id`, `person_entity_id`, `feature_version`, feature columns, `computed_at`

8. **`scores`**
   - `score_id`, `person_entity_id`, `total_score`, category sub-scores, `score_confidence`, `model_version`, `computed_at`

9. **`classifications`**
   - `classification_id`, `person_entity_id`, `tier`, `override_flag`, `override_reason`, `assigned_at`

10. **`routing_actions`**
    - `action_id`, `person_entity_id`, `queue_id`, `agent_profile`, `script_id`, `nurture_flow_id`, `scheduled_for`, `status`

11. **`activity_log`** (immutable audit)
    - `event_id`, `person_entity_id`, `event_type`, `event_payload_json`, `actor_type` (system/user), `created_at`

12. **`outcomes`**
    - `outcome_id`, `person_entity_id`, `call_disposition`, `qualified_flag`, `meeting_booked`, `deal_closed`, `deal_value`, `recorded_at`

13. **`consent_preferences`**
    - `person_entity_id`, `contact_channel`, `consent_status`, `lawful_basis`, `updated_at`

14. **`suppression_list`**
    - phone/email/entity IDs, do-not-contact reasons, legal hold flags.

---

## E. Scoring framework (100 points)

> Use rule-based weighted scoring first. Optionally add ML uplift score as a separate field, never as the only determinant.

### Category weights
1. **Professional status (20 pts)**
2. **Business ownership & leadership (20 pts)**
3. **Property/area/asset proxy signals (15 pts)**
4. **Digital/public presence (10 pts)**
5. **Reputation/media/influence (10 pts)**
6. **Liquidity likelihood (15 pts)**
7. **Decision-maker probability (10 pts)**

Total = 100

### 1) Professional status (0–20)
**Inputs:** job title, seniority keywords, employer size/prestige, profession type.
- 16–20: C-suite, partner, senior specialist in high-income profession, large firm executive.
- 8–15: mid-senior manager, established professional.
- 1–7: junior role or unclear title.
- 0: unemployed/student/unsupported.

**Missing data handling:** default 6 with low confidence penalty.

### 2) Business ownership & leadership (0–20)
**Inputs:** founder/director/officer records, shareholding proxies, number of active entities.
- 17–20: founder + multi-entity director or controlling owner.
- 9–16: single business owner/director.
- 1–8: non-owner employee.
- 0: contradictory/no ownership evidence.

**Missing data:** default 5.

### 3) Property/area/asset signals (0–15)
**Inputs:** suburb affluence index, lawful property ownership signals, premium postcode clustering.
- 12–15: multiple strong area/asset indicators.
- 6–11: one moderate indicator.
- 1–5: weak area signal only.
- 0: no support.

**Guardrail:** never infer exact wealth from a single property indicator.

### 4) Digital/public presence (0–10)
**Inputs:** verified professional profile, company bio, speaking listings.
- 8–10: consistent high-quality presence.
- 4–7: moderate professional footprint.
- 1–3: sparse but valid.
- 0: unverifiable.

### 5) Reputation/media/influence (0–10)
**Inputs:** credible news mentions, industry awards, board/advisory roles.
- 8–10: recurring credible coverage/recognized influence.
- 4–7: occasional credible mentions.
- 1–3: minimal references.
- 0: none.

### 6) Liquidity likelihood (0–15)
**Inputs:** role compensation proxies, business scale proxies, transaction/news events (exit/funding), professional tenure.
- 12–15: multiple strong liquidity proxies.
- 6–11: moderate indications.
- 1–5: weak indicators.
- 0: no evidence.

### 7) Decision-maker probability (0–10)
**Inputs:** title authority, ownership status, signing authority proxy, seniority stability.
- 8–10: clear buyer authority.
- 4–7: influencer with partial authority.
- 1–3: likely non-decision-maker.
- 0: clearly non-buying role.

---

### Confidence scoring (separate from 100)
Compute `score_confidence` (0–1) using:
- Identity certainty.
- Number of independent corroborating sources.
- Source quality/reliability.
- Data recency.
- Internal consistency (absence of conflicts).

**Bands:**
- High: >=0.80
- Medium: 0.60–0.79
- Low: <0.60

### Weak vs strong signal examples
- **Strong:** registered director + C-suite title + premium area + credible media source concordance.
- **Weak:** social-only luxury photo, no identity match, no professional corroboration.

### Missing data policy
- Use conservative defaults, reduce confidence, avoid auto-disqualifying solely for missing footprint.
- Route high-score/low-confidence leads to manual review instead of outright rejection.

---

## F. Decision logic (classification + routing)

### Tier assignment rules

1. **Tier 1 – Immediate call priority**
   - `total_score >= 80` AND `score_confidence >= 0.75` AND no compliance block.
   - Route: VIP dial queue within 15 minutes, senior agent, high-value script.

2. **Tier 2 – Qualified, call soon**
   - `65 <= total_score < 80` AND `score_confidence >= 0.65`.
   - Route: same-day queue, standard qualified script.

3. **Tier 3 – Nurture / delayed follow-up**
   - `50 <= total_score < 65` OR medium score with medium confidence.
   - Route: WhatsApp/email nurture, callback in 7–21 days.

4. **Tier 4 – Manual review**
   - High potential but low confidence:
     - `total_score >= 70` AND `score_confidence < 0.65`
     - Identity conflict present
     - Source contradictions
   - Route: analyst verification task SLA 24h.

5. **Tier 5 – Disqualify**
   - `total_score < 50` OR explicit suppression/legal disqualifier/non-target persona.
   - Route: no outbound; log reason code.

### Override rules (hard controls)
- **Always disqualify/suppress:** opt-out, do-not-call, legal block, fraudulent record.
- **Always manual review:** possible high-value identity collision, conflicting ownership data, sanctions/PEP risk checks (if integrated).
- **Promote rule:** known referral from trusted partner can lift one tier but must keep audit note.

---

## G. Automation stack suggestions (practical)

### CRM / Sales engagement
- Salesforce / HubSpot / Zoho CRM + dialer (Aircall, Five9, Genesys, Talkdesk).

### Workflow orchestration
- Temporal / n8n / Make / Zapier for lightweight; prefer Temporal for robust retries/state.

### Enrichment providers (licensed/public)
- Business registries APIs (country-specific), company intelligence providers, professional data providers, reputable news APIs.
- Use provider abstraction layer to avoid lock-in.

### Rules + scoring engine
- DecisionRules / Open Policy Agent / custom Python service.
- Store scoring config in versioned YAML/DB tables for ops-editable thresholds.

### LLM layer (assistive, not sole decision-maker)
- Use LLM for:
  - Entity disambiguation support notes.
  - Unstructured text extraction from biographies/news.
  - Explainability summaries for agents.
- Keep final tiering under deterministic rules + auditable scores.

### Datastores
- OLTP: PostgreSQL.
- Search/indexing: Elasticsearch/OpenSearch.
- Warehouse/BI: BigQuery/Snowflake/Redshift.
- Cache/queue: Redis + Kafka/SQS.

### Audit & observability
- Immutable audit log table + object storage snapshots.
- Metrics: queue latency, enrichment hit-rate, precision by tier, conversion by score band.
- Dashboards: Metabase/Power BI/Looker.

### Agent interface
- Single-pane lead card:
  - score, confidence, top reasons, disqualifier flags, recommended script, next best action.

---

## H. Edge cases handling

1. **Duplicate leads**
   - Use deterministic keys first; merge probabilistically with threshold.
   - Preserve source lineage; never destroy raw records.

2. **Identical names**
   - Require extra anchors (phone/email/company/location).
   - If unresolved, Tier 4 manual review.

3. **Missing employer data**
   - Backfill via domain/company inference where lawful.
   - Reduce confidence, do not auto-disqualify.

4. **No digital footprint**
   - Could still be affluent/private.
   - Keep neutral score defaults; rely on registry/property/geography/business data.

5. **Conflicting information across sources**
   - Apply source reliability hierarchy and recency rules.
   - Mark conflict flag and reduce confidence.

6. **Very wealthy but low-visibility individuals**
   - Emphasize ownership, registry, and area signals over social visibility.
   - Manual promotion path from Tier 4 when evidence is strong but sparse.

7. **False luxury signals**
   - Ignore vanity/social-only cues unless corroborated by reputable sources.

8. **Looks rich but not a decision-maker**
   - Decision-maker probability can cap final tier (e.g., max Tier 3 unless owner/executive evidence).

---

## I. Compliance safeguards (what system must never do)

1. Never use protected characteristics (race, religion, health, political views, etc.) for scoring.
2. Never buy or use unlawfully obtained data.
3. Never scrape behind authentication or violate source terms.
4. Never infer exact net worth from weak proxies.
5. Never auto-contact records on suppression/opt-out lists.
6. Never hide model/rule rationale from audit.
7. Never retain unnecessary personal data beyond retention policy.
8. Never let LLM fabricate facts; all asserted signals must have source records.

### POPIA-aware controls
- Purpose limitation and lawful basis tracking per source.
- Data minimization by feature-level retention windows.
- Data subject rights workflow (access, correction, deletion where applicable).
- Role-based access controls and field-level masking.
- Cross-border transfer safeguards and vendor DPAs.

---

## J. MVP build plan

### MVP (first 6–8 weeks): “Operational triage fast”
**Build now:**
1. Intake + normalization + dedupe.
2. Basic identity resolution (deterministic + simple fuzzy).
3. 3–5 enrichment connectors (company registry, professional profile, basic news).
4. Rule-based scoring v1 (100-point framework above).
5. Tier routing to dial queues + manual review queue.
6. Audit log with reason codes and source tracking.
7. Basic dashboard: leads by tier, call outcomes, conversion.

**Why:** immediate agent efficiency gains and explainable prioritization.

### Version 2 (next 6–10 weeks): “Quality & conversion lift”
1. Add confidence calibration and source reliability weighting.
2. Add nurture automation (WhatsApp/email sequences by tier/persona).
3. Add richer override governance and QA workflow.
4. Implement feedback-driven threshold tuning.
5. Add agent script personalization based on signal profile.

### Version 3 (quarterly scale): “Predictive optimization & governance maturity”
1. Add ML propensity model as secondary signal (not replacement).
2. Drift monitoring and automated retraining cadence.
3. Multi-region compliance policies and retention automation.
4. Revenue attribution by feature/source for budget optimization.
5. Advanced simulation tool for changing weights/thresholds before deployment.

---

## Implementation notes for sales ops teams

- Keep scoring weights in editable config with approval workflow.
- Run weekly scorecard review: Tier precision, false positives, no-contact compliance rate.
- Start conservative on auto-disqualify; prefer manual review for ambiguous high-potential leads.
- Train agents to use “top 3 reasons” from score breakdown in call openers.

This blueprint is designed for real deployment: deterministic where it matters, probabilistic where helpful, and always auditable.
