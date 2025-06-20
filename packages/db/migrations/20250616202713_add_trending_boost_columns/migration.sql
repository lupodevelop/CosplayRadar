-- AlterTable
ALTER TABLE "anilist_trending" ADD COLUMN     "character_gender" TEXT,
ADD COLUMN     "gender_boost" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
ADD COLUMN     "top_trending_series" TEXT,
ADD COLUMN     "total_boost_multiplier" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
ADD COLUMN     "weekly_trending_boost" DOUBLE PRECISION NOT NULL DEFAULT 1.0;
