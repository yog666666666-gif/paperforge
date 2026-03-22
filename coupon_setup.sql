-- Run this in Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste → Run

CREATE TABLE IF NOT EXISTS coupons (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('Basic','Medium','Advanced')),
    price       INTEGER NOT NULL,
    active      BOOLEAN DEFAULT true,
    used        BOOLEAN DEFAULT false,
    used_at     TIMESTAMPTZ,
    used_by     TEXT,
    used_for    TEXT,
    created_at  TIMESTAMPTZ DEFAULT now(),
    expires_at  TIMESTAMPTZ
);

-- 50 Basic coupons @ ₹999
INSERT INTO coupons (code, tier, price)
SELECT 'BASIC' || LPAD(generate_series::text, 3, '0'), 'Basic', 999
FROM generate_series(1, 50);

-- 50 Medium coupons @ ₹1,999
INSERT INTO coupons (code, tier, price)
SELECT 'MEDIUM' || LPAD(generate_series::text, 3, '0'), 'Medium', 1999
FROM generate_series(1, 50);

-- 50 Advanced coupons @ ₹4,999
INSERT INTO coupons (code, tier, price)
SELECT 'ADVANCED' || LPAD(generate_series::text, 3, '0'), 'Advanced', 4999
FROM generate_series(1, 50);

-- Your personal coupon
INSERT INTO coupons (code, tier, price)
VALUES ('YOGESH9999', 'Advanced', 0);

-- To view all unused coupons:
-- SELECT code, tier, price FROM coupons WHERE used=false ORDER BY tier, code;

-- To mark a coupon as a gift (for beta users):
-- UPDATE coupons SET active=true WHERE code='BASIC001';
