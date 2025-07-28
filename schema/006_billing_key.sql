-- --------------------------------------------------
-- Migration 006: Add billing_key column to user table
-- --------------------------------------------------
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS billing_key TEXT; 