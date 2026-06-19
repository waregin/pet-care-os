-- 005: seed Samson's allergy panel (from his test results). Known facts, like Troy's
-- rejections in 002 -- encoded as SQL so a fresh `migrate` reproduces the full known state.
-- `score` > 100 indicates an allergy; environmental/contamination rows (tree/grass/weed/staph/
-- fungi) are intentional avoids, not dietary. Rice (676) is the standout.
INSERT INTO pet_allergens (pet_id, allergen, category, score, source)
SELECT (SELECT id FROM pets WHERE name = 'Samson'), v.allergen, v.category, v.score, 'panel'
FROM (VALUES
    ('alfalfa', 'dietary', '118'),
    ('kelp', 'dietary', '107'),
    ('rice', 'dietary', '676'),
    ('corn', 'dietary', '127'),
    ('peanut', 'dietary', '144'),
    ('spinach', 'dietary', '113'),
    ('flax', 'dietary', '179'),
    ('pumpkin', 'dietary', '116'),
    ('tomato', 'dietary', '153'),
    ('staph', 'staph', '131'),
    ('Candida Albicans', 'fungi', '496'),
    ('acacia', 'tree', '204'),
    ('alder', 'tree', '113'),
    ('cypress', 'tree', '363'),
    ('elm', 'tree', '124'),
    ('mulberry', 'tree', '105'),
    ('oak', 'tree', '136'),
    ('olive', 'tree', '130'),
    ('pecan/hickory', 'tree', '117'),
    ('privet', 'tree', '143'),
    ('bahia', 'grasses', '113'),
    ('Bermuda', 'grasses', '111'),
    ('bluegrass/june grass', 'grasses', '106'),
    ('johnson grass', 'grasses', '106'),
    ('saltgrass/vernal', 'grasses', '102'),
    ('timothy', 'grasses', '129'),
    ('wheat', 'grasses', '93'),
    ('dandelion', 'weeds', '127'),
    ('dock/sheep sorrel', 'weeds', '136'),
    ('english plantain', 'weeds', '147'),
    ('pigweed', 'weeds', '145'),
    ('ragweed', 'weeds', '110'),
    ('sage', 'weeds', '235')
) AS v(allergen, category, score)
ON CONFLICT (pet_id, allergen) DO UPDATE
    SET score = EXCLUDED.score, category = EXCLUDED.category,
        source = EXCLUDED.source, updated_at = now();
