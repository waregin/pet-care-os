-- 003: known facts + a home for Samson's allergy panel.

-- Fact (confirmed): every food in the current rotation is SAFE for Samson.
-- Mark Samson 'safe' on all currently-cataloged foods. (At migration time that's the 15 seeded.)
INSERT INTO assessments (pet_id, food_id, safety)
SELECT (SELECT id FROM pets WHERE name = 'Samson'), f.id, 'safe'
FROM foods f
ON CONFLICT (pet_id, food_id) DO UPDATE SET safety = 'safe', updated_at = now();

-- Samson's allergy panel: allergen + score (kept as text to preserve whatever the panel reports —
-- numeric IgE, class label, etc.). This is the manual home for the data now; automated
-- food<->allergen matching to drive the safety gate is a later upgrade (see backlog issue #4).
CREATE TABLE pet_allergens (
    pet_id      INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    allergen    TEXT NOT NULL,
    score       TEXT,           -- raw score/class from the panel; nullable
    source      TEXT NOT NULL DEFAULT 'manual',
    note        TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (pet_id, allergen)
);
