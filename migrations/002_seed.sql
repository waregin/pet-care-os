-- Seed: the three cats and the foods currently in rotation (from the 6/19 schedule sheet).
-- Honest seed: we record only what's actually known. Troy's three rejections are recorded;
-- Samson's allergy verdicts and the rest of the acceptance grades are left for manual entry
-- (that capture IS the point of v1). Brand/form filled only where the name makes it certain.

INSERT INTO pets (name, species, calories_per_meal, can_cap, is_safety_gate, is_acceptance_gate, notes) VALUES
    ('Troy',   'cat', 150, TRUE,  FALSE, TRUE,  'Picky one. One full 5.5/6 oz can or 150 kcal, whichever is smaller. Acceptance gate: decides "buy it again".'),
    ('Gwen',   'cat', 100, FALSE, FALSE, FALSE, 'Chunky one. 100 kcal/meal. Not a reorder gate.'),
    ('Samson', 'cat', 150, FALSE, TRUE,  FALSE, 'The one with ~30 allergies; trending chunky (target ~125-150 kcal). Safety gate: decides "safe to buy at all".');

-- Foods in the current rotation. Dave's items: brand set, "dave's " prefix dropped from name.
INSERT INTO foods (brand, name, form) VALUES
    (NULL,              'Mack & Jack',            NULL),
    (NULL,              'catalina catch',         NULL),
    (NULL,              'splash dance',           NULL),
    (NULL,              'glam & punk',            NULL),
    (NULL,              'Mideast Feast',          NULL),
    (NULL,              'Monterey medley',        NULL),
    ('Dave''s Pet Food', 'chicken & whitefish',          NULL),
    ('Dave''s Pet Food', 'shredded salmon',              'shredded'),
    ('Dave''s Pet Food', 'shredded chicken',             'shredded'),
    ('Dave''s Pet Food', 'tuna & shrimp',                NULL),
    ('Dave''s Pet Food', 'tuna & chicken',               NULL),
    ('Dave''s Pet Food', 'tuna & salmon',                NULL),
    ('Dave''s Pet Food', 'saucey pate chicken & duck',   'pate'),
    ('Dave''s Pet Food', 'chicken & chicken liver pate', 'pate'),
    ('Dave''s Pet Food', 'fisherman''s stew',            'stew');

-- Known fact: Troy rejects these three (Not Approved). This is what keeps them off the reorder list.
INSERT INTO assessments (pet_id, food_id, acceptance, note)
SELECT (SELECT id FROM pets WHERE name = 'Troy'), f.id, 'rejects', 'Not Approved by Troy'
FROM foods f
WHERE f.brand = 'Dave''s Pet Food'
  AND f.name IN ('saucey pate chicken & duck', 'chicken & chicken liver pate', 'fisherman''s stew');
