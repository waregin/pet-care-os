-- 004: allergy panels carry a category (dietary / environmental / etc.), which matters because
-- not all reactivities are food-ingredient allergies — some are pollen/contamination avoids.
-- The dietary subset is what later food<->ingredient matching (#4) will key on.
ALTER TABLE pet_allergens ADD COLUMN category TEXT;
