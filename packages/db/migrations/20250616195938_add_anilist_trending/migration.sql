-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('CREATOR', 'ADMIN');

-- CreateEnum
CREATE TYPE "SubscriptionStatus" AS ENUM ('FREE', 'PREMIUM', 'CANCELED');

-- CreateEnum
CREATE TYPE "PlanType" AS ENUM ('FREE', 'PREMIUM');

-- CreateEnum
CREATE TYPE "Category" AS ENUM ('ANIME', 'MANGA', 'VIDEOGAME', 'MOVIE', 'TV_SHOW', 'COMIC', 'OTHER');

-- CreateEnum
CREATE TYPE "Platform" AS ENUM ('REDDIT', 'TWITTER', 'INSTAGRAM', 'TIKTOK', 'ZEROCHAN', 'OTHER');

-- CreateEnum
CREATE TYPE "TrendRegion" AS ENUM ('GLOBAL', 'US', 'JP', 'IT', 'UK', 'DE', 'FR', 'BR', 'KR', 'CA', 'AU', 'MX');

-- CreateEnum
CREATE TYPE "KeywordType" AS ENUM ('COSPLAY', 'CHARACTER', 'COSTUME', 'FANART', 'FIGURE', 'MERCH', 'GENERAL');

-- CreateEnum
CREATE TYPE "QueryVolume" AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH');

-- CreateEnum
CREATE TYPE "AnimeStatus" AS ENUM ('NOT_YET_RELEASED', 'RELEASING', 'FINISHED', 'CANCELLED', 'HIATUS');

-- CreateEnum
CREATE TYPE "MediaFormat" AS ENUM ('TV', 'TV_SHORT', 'MOVIE', 'SPECIAL', 'OVA', 'ONA', 'MUSIC', 'MANGA', 'NOVEL', 'ONE_SHOT');

-- CreateEnum
CREATE TYPE "AnimeSeason" AS ENUM ('SPRING', 'SUMMER', 'FALL', 'WINTER');

-- CreateEnum
CREATE TYPE "MediaSource" AS ENUM ('ORIGINAL', 'MANGA', 'LIGHT_NOVEL', 'VISUAL_NOVEL', 'VIDEO_GAME', 'OTHER');

-- CreateEnum
CREATE TYPE "DataQuality" AS ENUM ('ANILIST_HYBRID', 'FALLBACK', 'NO_DATA', 'MOCK');

-- CreateEnum
CREATE TYPE "TrendCategory" AS ENUM ('RISING', 'STABLE', 'DECLINING', 'VIRAL', 'EMERGING', 'BREAKOUT', 'SEASONAL');

-- CreateEnum
CREATE TYPE "BreakoutLevel" AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'IMMINENT');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "name" TEXT,
    "email" TEXT NOT NULL,
    "emailVerified" TIMESTAMP(3),
    "image" TEXT,
    "password" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'CREATOR',
    "subscription" "SubscriptionStatus" NOT NULL DEFAULT 'FREE',
    "plan" "PlanType" NOT NULL DEFAULT 'FREE',
    "username" TEXT,
    "bio" TEXT,
    "avatar" TEXT,
    "website" TEXT,
    "socialLinks" JSONB,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "accounts" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "provider_account_id" TEXT NOT NULL,
    "refresh_token" TEXT,
    "access_token" TEXT,
    "expires_at" INTEGER,
    "token_type" TEXT,
    "scope" TEXT,
    "id_token" TEXT,
    "session_state" TEXT,

    CONSTRAINT "accounts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sessions" (
    "id" TEXT NOT NULL,
    "session_token" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "verificationtokens" (
    "identifier" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL
);

-- CreateTable
CREATE TABLE "characters" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "series" TEXT NOT NULL,
    "category" "Category" NOT NULL,
    "difficulty" INTEGER NOT NULL DEFAULT 1,
    "popularity" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "imageUrl" TEXT,
    "description" TEXT,
    "tags" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "fandom" TEXT,
    "gender" TEXT,
    "popularityScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "sourceUrl" TEXT,
    "anilistId" INTEGER,
    "media_title" TEXT,
    "source" TEXT DEFAULT 'jikan',

    CONSTRAINT "characters_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "anilist_trending" (
    "id" TEXT NOT NULL,
    "character_id" TEXT NOT NULL,
    "trending_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trending_category" "TrendCategory" NOT NULL DEFAULT 'STABLE',
    "character_favourites" INTEGER NOT NULL DEFAULT 0,
    "normalized_favourites" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "avg_series_trending" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "total_series" INTEGER NOT NULL DEFAULT 0,
    "new_series_count" INTEGER NOT NULL DEFAULT 0,
    "new_series_boost_applied" BOOLEAN NOT NULL DEFAULT false,
    "algorithm_version" TEXT NOT NULL DEFAULT '1.0',
    "trending_weight" DOUBLE PRECISION NOT NULL DEFAULT 0.70,
    "favourites_weight" DOUBLE PRECISION NOT NULL DEFAULT 0.30,
    "new_series_boost_multiplier" DOUBLE PRECISION NOT NULL DEFAULT 2.50,
    "data_quality" "DataQuality" NOT NULL DEFAULT 'ANILIST_HYBRID',
    "calculated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_updated" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "anilist_trending_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "trend_data" (
    "id" TEXT NOT NULL,
    "character_id" TEXT NOT NULL,
    "platform" "Platform" NOT NULL,
    "mentions" INTEGER NOT NULL DEFAULT 0,
    "engagement" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "sentiment" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "date" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "trend_data_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "google_trend_data" (
    "id" TEXT NOT NULL,
    "character_id" TEXT NOT NULL,
    "region" "TrendRegion" NOT NULL DEFAULT 'GLOBAL',
    "keyword_type" "KeywordType" NOT NULL,
    "keyword" TEXT NOT NULL,
    "trend_7d" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trend_30d" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trend_90d" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "confidence" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "query_volume" "QueryVolume" NOT NULL DEFAULT 'LOW',
    "date" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "google_trend_data_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "trend_summary" (
    "id" TEXT NOT NULL,
    "character_id" TEXT NOT NULL,
    "global_cosplay_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "global_character_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "global_shopping_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "us_cosplay_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "jp_character_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "it_cosplay_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "overall_trend_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "cosplay_trend_score" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "rising_markets" JSONB,
    "best_market" "TrendRegion",
    "last_updated" TIMESTAMP(3) NOT NULL,
    "data_quality" DOUBLE PRECISION NOT NULL DEFAULT 1.0,

    CONSTRAINT "trend_summary_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "anime_releases" (
    "id" TEXT NOT NULL,
    "anilistId" INTEGER,
    "malId" INTEGER,
    "title" TEXT NOT NULL,
    "englishTitle" TEXT,
    "nativeTitle" TEXT,
    "status" "AnimeStatus" NOT NULL DEFAULT 'NOT_YET_RELEASED',
    "format" "MediaFormat" NOT NULL DEFAULT 'TV',
    "startDate" TIMESTAMP(3),
    "endDate" TIMESTAMP(3),
    "season" "AnimeSeason",
    "seasonYear" INTEGER,
    "episodes" INTEGER,
    "duration" INTEGER,
    "source" "MediaSource",
    "genres" TEXT[],
    "tags" TEXT[],
    "popularity" INTEGER NOT NULL DEFAULT 0,
    "meanScore" DOUBLE PRECISION,
    "favourites" INTEGER NOT NULL DEFAULT 0,
    "coverImage" TEXT,
    "bannerImage" TEXT,
    "description" TEXT,
    "siteUrl" TEXT,
    "isNew" BOOLEAN NOT NULL DEFAULT false,
    "isUpcoming" BOOLEAN NOT NULL DEFAULT false,
    "isTrending" BOOLEAN NOT NULL DEFAULT false,
    "trendRank" INTEGER,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lastChecked" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "anime_releases_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "anime_release_trends" (
    "id" TEXT NOT NULL,
    "anime_release_id" TEXT NOT NULL,
    "popularity" INTEGER NOT NULL DEFAULT 0,
    "favourites" INTEGER NOT NULL DEFAULT 0,
    "trendRank" INTEGER,
    "googleTrendScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "momentumScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "anticipationScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "date" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "anime_release_trends_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "character_trend_analysis" (
    "id" TEXT NOT NULL,
    "character_id" TEXT NOT NULL,
    "isNew" BOOLEAN NOT NULL DEFAULT false,
    "isUpcoming" BOOLEAN NOT NULL DEFAULT false,
    "isTrendingUp" BOOLEAN NOT NULL DEFAULT false,
    "isBreakout" BOOLEAN NOT NULL DEFAULT false,
    "popularityScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trendScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "momentumScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "anticipationScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "overallScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trendDelta7d" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "trendDelta30d" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "peakScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "peakDate" TIMESTAMP(3),
    "trendCategory" "TrendCategory" NOT NULL DEFAULT 'STABLE',
    "breakoutPotential" "BreakoutLevel" NOT NULL DEFAULT 'LOW',
    "seasonalFactor" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "confidence" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "dataQuality" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lastAnalyzed" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "character_trend_analysis_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "character_weekly_trends" (
    "id" TEXT NOT NULL,
    "character_trend_id" TEXT NOT NULL,
    "weekStart" TIMESTAMP(3) NOT NULL,
    "weekEnd" TIMESTAMP(3) NOT NULL,
    "cosplayTrendScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "characterTrendScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "generalTrendScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "anilistPopularity" INTEGER NOT NULL DEFAULT 0,
    "anilistFavourites" INTEGER NOT NULL DEFAULT 0,
    "redditMentions" INTEGER NOT NULL DEFAULT 0,
    "twitterMentions" INTEGER NOT NULL DEFAULT 0,
    "weeklyScore" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "growthRate" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "volatility" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "weeklyCategory" "TrendCategory" NOT NULL DEFAULT 'STABLE',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "character_weekly_trends_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_AnimeReleaseToCharacter" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE UNIQUE INDEX "accounts_provider_provider_account_id_key" ON "accounts"("provider", "provider_account_id");

-- CreateIndex
CREATE UNIQUE INDEX "sessions_session_token_key" ON "sessions"("session_token");

-- CreateIndex
CREATE UNIQUE INDEX "verificationtokens_token_key" ON "verificationtokens"("token");

-- CreateIndex
CREATE UNIQUE INDEX "verificationtokens_identifier_token_key" ON "verificationtokens"("identifier", "token");

-- CreateIndex
CREATE INDEX "anilist_trending_trending_score_idx" ON "anilist_trending"("trending_score");

-- CreateIndex
CREATE INDEX "anilist_trending_trending_category_idx" ON "anilist_trending"("trending_category");

-- CreateIndex
CREATE INDEX "anilist_trending_new_series_boost_applied_idx" ON "anilist_trending"("new_series_boost_applied");

-- CreateIndex
CREATE INDEX "anilist_trending_calculated_at_idx" ON "anilist_trending"("calculated_at");

-- CreateIndex
CREATE UNIQUE INDEX "anilist_trending_character_id_key" ON "anilist_trending"("character_id");

-- CreateIndex
CREATE INDEX "google_trend_data_character_id_region_keyword_type_idx" ON "google_trend_data"("character_id", "region", "keyword_type");

-- CreateIndex
CREATE INDEX "google_trend_data_region_keyword_type_trend_7d_idx" ON "google_trend_data"("region", "keyword_type", "trend_7d");

-- CreateIndex
CREATE INDEX "google_trend_data_date_idx" ON "google_trend_data"("date");

-- CreateIndex
CREATE UNIQUE INDEX "google_trend_data_character_id_region_keyword_type_keyword_key" ON "google_trend_data"("character_id", "region", "keyword_type", "keyword");

-- CreateIndex
CREATE UNIQUE INDEX "trend_summary_character_id_key" ON "trend_summary"("character_id");

-- CreateIndex
CREATE UNIQUE INDEX "anime_releases_anilistId_key" ON "anime_releases"("anilistId");

-- CreateIndex
CREATE INDEX "anime_releases_season_seasonYear_idx" ON "anime_releases"("season", "seasonYear");

-- CreateIndex
CREATE INDEX "anime_releases_startDate_idx" ON "anime_releases"("startDate");

-- CreateIndex
CREATE INDEX "anime_releases_status_isUpcoming_idx" ON "anime_releases"("status", "isUpcoming");

-- CreateIndex
CREATE INDEX "anime_releases_isTrending_trendRank_idx" ON "anime_releases"("isTrending", "trendRank");

-- CreateIndex
CREATE INDEX "anime_release_trends_anime_release_id_date_idx" ON "anime_release_trends"("anime_release_id", "date");

-- CreateIndex
CREATE UNIQUE INDEX "character_trend_analysis_character_id_key" ON "character_trend_analysis"("character_id");

-- CreateIndex
CREATE INDEX "character_weekly_trends_weekStart_weekEnd_idx" ON "character_weekly_trends"("weekStart", "weekEnd");

-- CreateIndex
CREATE UNIQUE INDEX "character_weekly_trends_character_trend_id_weekStart_key" ON "character_weekly_trends"("character_trend_id", "weekStart");

-- CreateIndex
CREATE UNIQUE INDEX "_AnimeReleaseToCharacter_AB_unique" ON "_AnimeReleaseToCharacter"("A", "B");

-- CreateIndex
CREATE INDEX "_AnimeReleaseToCharacter_B_index" ON "_AnimeReleaseToCharacter"("B");

-- AddForeignKey
ALTER TABLE "accounts" ADD CONSTRAINT "accounts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "anilist_trending" ADD CONSTRAINT "anilist_trending_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trend_data" ADD CONSTRAINT "trend_data_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "google_trend_data" ADD CONSTRAINT "google_trend_data_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trend_summary" ADD CONSTRAINT "trend_summary_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "anime_release_trends" ADD CONSTRAINT "anime_release_trends_anime_release_id_fkey" FOREIGN KEY ("anime_release_id") REFERENCES "anime_releases"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "character_trend_analysis" ADD CONSTRAINT "character_trend_analysis_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "character_weekly_trends" ADD CONSTRAINT "character_weekly_trends_character_trend_id_fkey" FOREIGN KEY ("character_trend_id") REFERENCES "character_trend_analysis"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_AnimeReleaseToCharacter" ADD CONSTRAINT "_AnimeReleaseToCharacter_A_fkey" FOREIGN KEY ("A") REFERENCES "anime_releases"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_AnimeReleaseToCharacter" ADD CONSTRAINT "_AnimeReleaseToCharacter_B_fkey" FOREIGN KEY ("B") REFERENCES "characters"("id") ON DELETE CASCADE ON UPDATE CASCADE;
