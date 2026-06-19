-- 007: ingest the two historical food sheets (merge & dedupe into the existing catalog).
-- Decisions (per owner): merge now / richer schema later (#issue); confident matches to the
-- seeded 15 are skipped; only "do not buy again" is imported as a current signal (do_not_buy),
-- all other years-old per-cat verdicts are intentionally skipped. All imported foods are safe
-- for Samson. can_size/form captured where obvious; cost/retailer/meal-split data is deferred
-- to the schema-expansion issue.
INSERT INTO foods (brand, name, form, can_size_oz, source, do_not_buy)
SELECT v.brand, v.name, v.form, v.can_size_oz, v.source, v.do_not_buy
FROM (VALUES
    ('Dave''s Pet Food', 'Naturally Healthy Grain-Free Tuna Entree in Gravy', NULL, NULL, 'import:56oz', FALSE),
    ('Weruva', 'BFF Cat Food - Tuna & Salmon Soulmates Recipe', NULL, NULL, 'import:56oz', FALSE),
    ('Weruva', 'BFF OMG Cat Food - Chicken & Lamb Selfie Cam', NULL, NULL, 'import:56oz', FALSE),
    ('Weruva', 'BFF OMG Cat Food - Chicken & Salmon Crazy 4 U', NULL, NULL, 'import:56oz', FALSE),
    ('Weruva', 'BFF OMG Cat Food - Duck & Tuna Lots O Luck', NULL, NULL, 'import:56oz', FALSE),
    ('Weruva', 'BFF Tuna & Chicken 4EVA in Gravy', NULL, NULL, 'import:56oz', FALSE),
    ('Freely', 'Rabbit Recipe Limited Ingredient Grain-Free', NULL, NULL, 'import:56oz', TRUE),
    ('Lotus', 'Just Juicy Venison Stew', 'stew', NULL, 'import:56oz', TRUE),
    ('Weruva', 'Cats in The Kitchen Cat Food - Lamb Burgini with Lamb', NULL, NULL, 'import:56oz', FALSE),
    ('Fussie Cat', 'Premium Tuna with Ocean Fish in Aspic', 'aspic', NULL, 'import:56oz', FALSE),
    ('Hound & Gatos', '98% Beef Grain-Free', NULL, NULL, 'import:56oz', TRUE),
    ('Hound & Gatos', '98% Lamb & Liver Formula Grain-Free', NULL, NULL, 'import:56oz', FALSE),
    ('Instinct', 'Limited Ingredient Diet Grain-Free Pate Real Rabbit Recipe', 'pate', NULL, 'import:56oz', FALSE),
    ('FirstMate', 'LID Salmon', NULL, NULL, 'import:56oz', TRUE),
    ('FirstMate', 'Limited Ingredient Turkey', NULL, NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Grain-Free Chicken', NULL, NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Grain-Free Turkey', NULL, NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Naturally Healthy Grain-Free Turkey & Giblets', NULL, NULL, 'import:56oz', TRUE),
    ('Earthborn Holistic', 'Chicken Jumble with Liver', NULL, NULL, 'import:56oz', TRUE),
    ('FirstMate', 'Limited Ingredient Cage-free Chicken', NULL, NULL, 'import:56oz', TRUE),
    ('Fromm', 'Four-Star Wet Cat Food - Grain Free Shredded Turkey', 'shredded', NULL, 'import:56oz', TRUE),
    ('Fussie Cat', 'Super Premium Chicken in Gravy', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Amazon Livin with Chicken & Chicken Liver in Gravy', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Asian Fusion with Tuna & Shirasu', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'BFF Cat Food - Tuna & Shrimp Sweethearts Recipe', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'BFF OMG Cat Food - Chicken & Turkey QT Patootie', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Cats in The Kitchen Cat Food - Chicken Frick ''A Zee with Chicken', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Cats in The Kitchen Cat Food - Fowl Ball with Chicken & Turkey', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Cats in The Kitchen Cat Food - Kitty Gone Wild with Wild Salmon', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Paw Lickin'' Chickin with Chicken in Gravy', NULL, NULL, 'import:56oz', TRUE),
    ('Weruva', 'Polynesian BBQ with Grilled Red Bigeye', NULL, NULL, 'import:56oz', FALSE),
    ('Dave''s Pet Food', 'Ahi Tuna Dinner with Chicken', NULL, NULL, 'import:56oz', TRUE),
    ('Fussie Cat', 'Premium Tuna Formula in Aspic', 'aspic', NULL, 'import:56oz', FALSE),
    ('Fussie Cat', 'Premium Tuna with Chicken Formula in Aspic', 'aspic', NULL, 'import:56oz', FALSE),
    ('Dave''s Pet Food', 'Cat''s Meow Chicken & Lamb Dinner Pate', 'pate', NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Cat''s Meow Beef & Duck Dunner Pate', 'pate', NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Cat''s Meow Beef & Lamb Dinner Pate', 'pate', NULL, 'import:56oz', TRUE),
    ('Dave''s Pet Food', 'Cat''s Meow Chicken & Duck Dinner Pate', 'pate', NULL, 'import:56oz', TRUE),
    ('American Journey Landmark', 'Mackeral & Tuna Recipe in Broth Grain-Free', NULL, 3, 'import:food_options', FALSE),
    ('American Journey Landmark', 'Tuna & Tilapia Recipe in Broth Grain-Free', NULL, 3, 'import:food_options', FALSE),
    ('Almo Nature Daily Complete', 'Tuna Dinner with Sardine in Broth', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature HQS Natural', 'Tuna with Anchovies in Broth Grain-Free', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Daily Complete', 'Tuna Dinner with Mackerel in Broth', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Classic Complete', 'Premium Chicken Recipe with Tuna in Gravy Grain-Free', NULL, 2.47, 'import:food_options', FALSE),
    ('Snappy Tom Lites', 'Tuna with Cheese', NULL, 5.5, 'import:food_options', FALSE),
    ('Almo Nature Daily Complete', 'Tuna Dinner with Shrimps in Broth', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Daily Complete', 'Tuna Dinner with Chicken in Broth', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Classic Complete', 'Premium Grain-Free Tuna Recipe with Salmon in Gravy', NULL, 2.47, 'import:food_options', FALSE),
    ('Snappy Tom Lites', 'Tuna with Shrimp & Calamari', NULL, 3, 'import:food_options', FALSE),
    ('Almo Nature Daily Complete', 'Tuna Dinner with Salmon in Broth', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Classic Complete', 'Premium Grain-Free Tuna Recipe with Shrimps in Gravy', NULL, 2.47, 'import:food_options', FALSE),
    ('Snappy Tom Lites', 'Tuna Flavor', NULL, 3, 'import:food_options', FALSE),
    ('Almo Nature Classic Complete', 'Premium Grain-Free Tuna Recipe with Chicken in Gravy', NULL, 2.47, 'import:food_options', FALSE),
    ('Almo Nature Classic Complete', 'Premium Grain-Free Tuna Recipe in Gravy', NULL, 2.47, 'import:food_options', FALSE),
    ('Snappy Tom Lites', 'Tuna with Crabmeat', NULL, 5.5, 'import:food_options', FALSE),
    ('Snappy Tom Lites', 'Tuna with Salmon', NULL, 5.5, 'import:food_options', FALSE),
    ('Merrick Purrfect Bistro', 'Salmon Recipe Pate Grain Free', 'pate', 5.5, 'import:food_options', FALSE),
    ('Merrick Purrfect Bistro', 'Tuna Recipe Pate Grain Free', 'pate', 5.5, 'import:food_options', FALSE),
    ('Merrick Purrfect Bistro', 'Surfin'' + Turfin'' Recipe Pate Grain Free', 'pate', 5.5, 'import:food_options', FALSE),
    ('ORIJEN', 'Tuna, Salmon + Beef Entree in Bone Broth', NULL, 5.5, 'import:food_options', FALSE),
    ('Purina Pro Plan', 'Focus Sensitive Skin & Stomach Tuna & Oat Meal Entree', NULL, 3, 'import:food_options', FALSE),
    ('Wellness CORE Signature Selects', 'Flaked Skipjack Tuna & Wild Salmon Entree in Broth Grain-Free', NULL, 5.3, 'import:food_options', FALSE),
    ('Wellness CORE Signature Selects', 'Flaked Skipjack Tuna & Shrimp Entree in Broth Grain-Free Natural', NULL, 5.3, 'import:food_options', FALSE)
) AS v(brand, name, form, can_size_oz, source, do_not_buy)
ON CONFLICT (brand, name) DO NOTHING;

-- Every imported food is safe for Samson.
INSERT INTO assessments (pet_id, food_id, safety)
SELECT (SELECT id FROM pets WHERE name = 'Samson'), f.id, 'safe'
FROM foods f
WHERE f.source LIKE 'import:%'
ON CONFLICT (pet_id, food_id) DO UPDATE SET safety = 'safe', updated_at = now();
