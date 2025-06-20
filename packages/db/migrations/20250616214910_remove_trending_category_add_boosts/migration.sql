/*
  Warnings:

  - You are about to drop the column `trending_category` on the `anilist_trending` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "anilist_trending_trending_category_idx";

-- AlterTable
ALTER TABLE "anilist_trending" DROP COLUMN "trending_category";

-- CreateIndex
CREATE INDEX "anilist_trending_character_gender_idx" ON "anilist_trending"("character_gender");

-- CreateIndex
CREATE INDEX "anilist_trending_weekly_trending_boost_idx" ON "anilist_trending"("weekly_trending_boost");
