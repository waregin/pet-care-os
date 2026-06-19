-- 006: a "do not buy again" decision is food-level (could be any cat, cost, etc.) and distinct
-- from `discontinued` (product gone) — so it gets its own flag, and drops the food from reorder.
ALTER TABLE foods ADD COLUMN do_not_buy BOOLEAN NOT NULL DEFAULT FALSE;

CREATE OR REPLACE VIEW reorderable_foods AS
SELECT
    f.id,
    f.brand,
    f.name,
    f.form,
    f.discontinued,
    (SELECT MAX(a.safety::text) FROM assessments a
       JOIN pets p ON p.id = a.pet_id
      WHERE a.food_id = f.id AND p.is_safety_gate)                              AS safety_gate_status,
    (SELECT MIN(a.acceptance::text) FROM assessments a
       JOIN pets p ON p.id = a.pet_id
      WHERE a.food_id = f.id AND p.is_acceptance_gate)                          AS acceptance_gate_status
FROM foods f
WHERE f.discontinued = FALSE
  AND f.do_not_buy = FALSE
  AND NOT EXISTS (
        SELECT 1 FROM assessments a
          JOIN pets p ON p.id = a.pet_id
         WHERE a.food_id = f.id AND p.is_safety_gate AND a.safety = 'unsafe')
  AND NOT EXISTS (
        SELECT 1 FROM assessments a
          JOIN pets p ON p.id = a.pet_id
         WHERE a.food_id = f.id AND p.is_acceptance_gate AND a.acceptance = 'rejects');
