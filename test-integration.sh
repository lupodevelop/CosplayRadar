#!/bin/bash

# Script per testare l'integrazione AniList completa

echo "🚀 Starting CosplayRadar AniList Integration Test"
echo "=================================================="

# Controllo se il server è già in esecuzione
if ! curl -s http://localhost:3000/api/hello > /dev/null 2>&1; then
    echo "❌ Server not running on localhost:3000"
    echo "Please start the server with: npm run dev"
    exit 1
fi

echo "✅ Server is running"

# Test 1: Endpoint characters con source=anilist
echo ""
echo "📋 Test 1: Characters endpoint with AniList source"
echo "---------------------------------------------------"
response=$(curl -s "http://localhost:3000/api/characters?source=anilist&limit=3")
if echo "$response" | grep -q '"source":"anilist"'; then
    echo "✅ AniList characters endpoint working"
    character_count=$(echo "$response" | grep -o '"name"' | wc -l | tr -d ' ')
    echo "   Found $character_count characters"
else
    echo "❌ AniList characters endpoint failed"
    echo "   Response: $response"
fi

# Test 2: Endpoint characters con gender filter
echo ""
echo "🚺 Test 2: Characters endpoint with gender filter"
echo "------------------------------------------------"
response=$(curl -s "http://localhost:3000/api/characters?source=anilist&gender=Female&limit=2")
if echo "$response" | grep -q '"gender":"Female"'; then
    echo "✅ Gender filter working"
else
    echo "❌ Gender filter failed"
    echo "   Response: $response"
fi

# Test 3: Admin sync status
echo ""
echo "📊 Test 3: Admin sync status"
echo "----------------------------"
response=$(curl -s -X POST http://localhost:3000/api/admin/sync \
    -H "Content-Type: application/json" \
    -d '{"action": "status"}')
if echo "$response" | grep -q '"totalCharacters"'; then
    echo "✅ Admin sync status working"
    total=$(echo "$response" | grep -o '"totalCharacters":[0-9]*' | cut -d':' -f2)
    echo "   Total characters in DB: $total"
else
    echo "❌ Admin sync status failed"
    echo "   Response: $response"
fi

# Test 4: AniList sync (solo se ci sono pochi personaggi)
echo ""
echo "🔄 Test 4: AniList sync test"
echo "----------------------------"
response=$(curl -s -X POST http://localhost:3000/api/admin/sync \
    -H "Content-Type: application/json" \
    -d '{"action": "sync", "source": "anilist"}')
if echo "$response" | grep -q '"success"'; then
    success=$(echo "$response" | grep -o '"success":[^,]*' | cut -d':' -f2)
    synced=$(echo "$response" | grep -o '"syncedCount":[0-9]*' | cut -d':' -f2)
    updated=$(echo "$response" | grep -o '"updatedCount":[0-9]*' | cut -d':' -f2)
    
    if [ "$success" = "true" ]; then
        echo "✅ AniList sync completed successfully"
        echo "   Synced: $synced, Updated: $updated"
    else
        echo "⚠️  AniList sync completed with errors"
        echo "   Synced: $synced, Updated: $updated"
        echo "   Response: $response"
    fi
else
    echo "❌ AniList sync failed"
    echo "   Response: $response"
fi

echo ""
echo "🎉 Integration test completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Visit http://localhost:3000/test-anilist to test the UI"
echo "   2. Visit http://localhost:3000/test-sync to test admin functions"
echo "   3. Visit http://localhost:3000/dashboard to see the main dashboard"
echo ""
