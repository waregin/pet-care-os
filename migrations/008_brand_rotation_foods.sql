-- 008: brand the six rotation foods that were seeded with NULL brand (002).
-- Weruva: Mack & Jack and Mideast Feast confirmed by the 56oz sheet; splash dance and
-- glam & punk (BFF line) per owner. Earthborn Holistic: catalina catch and Monterey medley
-- per owner. Guarded on brand IS NULL so this only touches the original rotation rows.
UPDATE foods SET brand = 'Weruva'
 WHERE brand IS NULL AND name IN ('Mack & Jack', 'Mideast Feast', 'splash dance', 'glam & punk');

UPDATE foods SET brand = 'Earthborn Holistic'
 WHERE brand IS NULL AND name IN ('catalina catch', 'Monterey medley');
