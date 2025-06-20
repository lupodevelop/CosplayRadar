// Dashboard completo per Google Trends
const runCompleteDashboard = async () => {
  console.log('🎯 ====== COSPLAYRADAR GOOGLE TRENDS DASHBOARD ====== 🎯\n');
  
  try {
    // 1. Sistema Status
    console.log('📊 SYSTEM STATUS');
    console.log('─'.repeat(50));
    
    const syncStatus = await fetch('http://localhost:3000/api/admin/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'status' })
    });
    const syncData = await syncStatus.json();
    
    const trendsStatus = await fetch('http://localhost:3000/api/admin/trends');
    const trendsData = await trendsStatus.json();
    
    console.log(`📈 Total Characters: ${syncData.stats.totalCharacters}`);
    console.log(`🔄 Total Trend Data: ${trendsData.stats.totalTrendData}`);
    console.log(`⚡ Recent Trends: ${trendsData.stats.recentTrendData}`);
    console.log(`🎯 Characters with Trends: ${trendsData.stats.charactersWithTrends}`);
    console.log(`📊 Avg Trend Score: ${trendsData.stats.avgTrendScore.toFixed(2)}`);
    
    // 2. Top Trends
    console.log('\n🏆 TOP COSPLAY TRENDS');
    console.log('─'.repeat(50));
    
    const topTrends = await fetch('http://localhost:3000/api/trends?keywordType=COSPLAY&limit=10');
    const topData = await topTrends.json();
    
    if (topData.data && topData.data.length > 0) {
      topData.data.forEach((trend, index) => {
        console.log(`${index + 1}. ${trend.character.name} (${trend.character.series})`);
        console.log(`   📊 Score: ${trend.trendScore} | 🎭 Difficulty: ${trend.character.difficulty} | ⚡ Confidence: ${(trend.confidence * 100).toFixed(1)}%`);
      });
    } else {
      console.log('No cosplay trends data available yet.');
    }
    
    // 3. Character Trends
    console.log('\n🎭 TOP CHARACTER TRENDS');
    console.log('─'.repeat(50));
    
    const charTrends = await fetch('http://localhost:3000/api/trends?keywordType=CHARACTER&limit=5');
    const charData = await charTrends.json();
    
    if (charData.data && charData.data.length > 0) {
      charData.data.forEach((trend, index) => {
        console.log(`${index + 1}. ${trend.character.name} (${trend.character.series})`);
        console.log(`   📊 Score: ${trend.trendScore} | 👤 Gender: ${trend.character.gender} | ⚡ Confidence: ${(trend.confidence * 100).toFixed(1)}%`);
      });
    } else {
      console.log('No character trends data available yet.');
    }
    
    // 4. Market Analysis
    console.log('\n📈 MARKET ANALYSIS');
    console.log('─'.repeat(50));
    
    const marketGaps = await fetch('http://localhost:3000/api/market-analysis?type=market-gaps');
    const gapsData = await marketGaps.json();
    
    if (gapsData.success) {
      console.log(`📊 Total Characters Analyzed: ${gapsData.data.totalCharacters}`);
      console.log(`👥 Gender Distribution:`);
      Object.entries(gapsData.data.distributions.gender).forEach(([gender, count]) => {
        console.log(`   ${gender}: ${count} (${((count / gapsData.data.totalCharacters) * 100).toFixed(1)}%)`);
      });
      
      console.log(`🎯 Difficulty Distribution:`);
      Object.entries(gapsData.data.distributions.difficulty).forEach(([diff, count]) => {
        console.log(`   Level ${diff}: ${count} characters`);
      });
      
      if (gapsData.data.marketGaps.underrepresentedDifficulties.length > 0) {
        console.log(`⚠️  Underrepresented Difficulties:`);
        gapsData.data.marketGaps.underrepresentedDifficulties.forEach(gap => {
          console.log(`   Level ${gap.difficulty}: ${gap.count} chars (${gap.percentage.toFixed(1)}%)`);
        });
      }
    }
    
    // 5. Filtering Examples
    console.log('\n🔍 FILTERING EXAMPLES');
    console.log('─'.repeat(50));
    
    // Filter per serie
    const attackOnTitan = await fetch('http://localhost:3000/api/trends?series=attack&limit=3');
    const aotData = await attackOnTitan.json();
    
    if (aotData.data && aotData.data.length > 0) {
      console.log('🏰 Attack on Titan Characters:');
      aotData.data.forEach(trend => {
        console.log(`   ${trend.character.name}: Score ${trend.trendScore} (${trend.keywordType})`);
      });
    }
    
    // 6. API Endpoints Summary
    console.log('\n🔗 AVAILABLE API ENDPOINTS');
    console.log('─'.repeat(50));
    console.log('📊 GET  /api/trends?keywordType=COSPLAY&limit=10');
    console.log('🎯 GET  /api/trends?series=naruto&region=GLOBAL');
    console.log('📈 GET  /api/market-analysis?type=market-overview');
    console.log('🏆 GET  /api/market-analysis?type=top-cosplay');
    console.log('🔍 GET  /api/market-analysis?type=market-gaps');
    console.log('⚙️  POST /api/admin/trends (update-all, update-batch, status)');
    console.log('🔄 POST /api/admin/sync (full-sync with trends)');
    console.log('🧪 POST /api/admin/test-data (populate-test-data)');
    
    console.log('\n✅ GOOGLE TRENDS INTEGRATION COMPLETE!');
    console.log('🚀 System ready for multi-dimensional trend analysis');
    
  } catch (error) {
    console.error('❌ Dashboard error:', error);
  }
};

runCompleteDashboard();
