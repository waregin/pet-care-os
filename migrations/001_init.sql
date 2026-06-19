-- Pet Care OS — Phase 1 schema: cat food catalog, per-cat assessments, reorder safety.
-- Conventions: PostgreSQL, idempotent-ish forward migrations applied in filename order.

-- Pets we feed. Phase 1 only needs cats, but the table is pet-general for later phases.
CREATE TABLE pets (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,
    species             TEXT NOT NULL DEFAULT 'cat',
    calories_per_meal   INTEGER,          -- target kcal/meal (catalog metadata; no portioning engine in v1)
    can_cap             BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = capped at one full can/meal regardless of kcal (Troy)
    -- Reorder gates. A food is reorderable only if it clears every gating pet:
    is_safety_gate      BOOLEAN NOT NULL DEFAULT FALSE,  -- this pet's allergies decide "safe to buy at all" (Samson)
    is_acceptance_gate  BOOLEAN NOT NULL DEFAULT FALSE,  -- this pet's pickiness decides "buy it again" (Troy)
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The catalog of cat food options. Scraper-ready: ChewyScraper (later) populates rows here.
-- Brand/form/protein/calories are nullable so manual entry never blocks on unknowns.
CREATE TABLE foods (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,        -- product/flavor name, e.g. "tuna & shrimp"
    brand           TEXT,                 -- e.g. "Dave's Pet Food" (NULL when unknown — do not guess)
    form            TEXT,                 -- pate / shredded / stew / etc.
    can_size_oz     NUMERIC(4,1),         -- e.g. 5.5
    calories_per_can INTEGER,
    -- Provenance: where this catalog row came from. 'manual' for v1; scrapers set their source.
    source          TEXT NOT NULL DEFAULT 'manual',
    source_url      TEXT,
    discontinued    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (brand, name)
);

-- How each cat rates / tolerates each food.
-- Two orthogonal axes so the two reorder gates stay independent:
--   acceptance = "will they eat it"  (Troy is the gate)
--   safety     = "is it allergen-safe" (Samson is the gate)
CREATE TYPE acceptance_status AS ENUM ('loves', 'eats', 'tolerates', 'rejects', 'never_tried');
CREATE TYPE safety_status     AS ENUM ('safe', 'unsafe', 'unknown');

CREATE TABLE assessments (
    pet_id      INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    food_id     INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    acceptance  acceptance_status NOT NULL DEFAULT 'never_tried',
    safety      safety_status     NOT NULL DEFAULT 'unknown',
    note        TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (pet_id, food_id)
);

CREATE INDEX idx_assessments_food ON assessments(food_id);

-- View: the v1 deliverable — "what is safe and accepted to (re)order right now?"
-- A food is reorderable when:
--   * no safety-gate pet has marked it 'unsafe', AND
--   * no acceptance-gate pet has marked it 'rejects'.
-- Unknowns do NOT exclude a food (you may not have tried it yet) but are surfaced so you can see risk.
CREATE VIEW reorderable_foods AS
SELECT
    f.id,
    f.brand,
    f.name,
    f.form,
    f.discontinued,
    -- worst safety verdict from any safety-gate pet (NULL if none recorded)
    (SELECT MAX(a.safety::text) FROM assessments a
       JOIN pets p ON p.id = a.pet_id
      WHERE a.food_id = f.id AND p.is_safety_gate)                              AS safety_gate_status,
    -- acceptance verdict from acceptance-gate pet(s)
    (SELECT MIN(a.acceptance::text) FROM assessments a
       JOIN pets p ON p.id = a.pet_id
      WHERE a.food_id = f.id AND p.is_acceptance_gate)                          AS acceptance_gate_status
FROM foods f
WHERE f.discontinued = FALSE
  AND NOT EXISTS (
        SELECT 1 FROM assessments a
          JOIN pets p ON p.id = a.pet_id
         WHERE a.food_id = f.id AND p.is_safety_gate AND a.safety = 'unsafe')
  AND NOT EXISTS (
        SELECT 1 FROM assessments a
          JOIN pets p ON p.id = a.pet_id
         WHERE a.food_id = f.id AND p.is_acceptance_gate AND a.acceptance = 'rejects');
