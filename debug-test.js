// Test script to debug maritime routing issues
const test = async () => {
  try {
    console.log('=== TESTING MARITIME ASSISTANT APIs ===\n');
    
    // Test 1: Health check
    console.log('1. Testing health endpoint...');
    const healthResponse = await fetch('http://127.0.0.1:8000/');
    console.log('Health status:', healthResponse.status, healthResponse.statusText);
    
    // Test 2: Location lookup
    console.log('\n2. Testing location lookup...');
    const rotterdamResponse = await fetch('http://127.0.0.1:8000/api/locations/global?query=rotterdam');
    const rotterdamData = await rotterdamResponse.json();
    console.log('Rotterdam data:', rotterdamData[0]);
    
    const hamburgResponse = await fetch('http://127.0.0.1:8000/api/locations/global?query=hamburg');
    const hamburgData = await hamburgResponse.json();
    console.log('Hamburg data:', hamburgData[0]);
    
    // Test 3: Route optimization
    console.log('\n3. Testing route optimization...');
    const routePayload = {
      origin: { lat: rotterdamData[0].latitude, lng: rotterdamData[0].longitude },
      destination: { lat: hamburgData[0].latitude, lng: hamburgData[0].longitude },
      vessel_type: 'container',
      optimization: 'fuel'
    };
    
    console.log('Route payload:', JSON.stringify(routePayload, null, 2));
    
    const routeResponse = await fetch('http://127.0.0.1:8000/routes/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(routePayload)
    });
    
    console.log('Route response status:', routeResponse.status, routeResponse.statusText);
    
    if (!routeResponse.ok) {
      const errorText = await routeResponse.text();
      console.error('Route optimization failed:', errorText);
      return;
    }
    
    const routeData = await routeResponse.json();
    console.log('\n=== ROUTE OPTIMIZATION RESULTS ===');
    console.log('Distance (nm):', routeData.distance_nm);
    console.log('Time (hours):', routeData.estimated_time_hours);
    console.log('Fuel (mt):', routeData.fuel_consumption_mt);
    console.log('Route type:', routeData.route_type);
    console.log('Number of waypoints:', routeData.route_points?.length);
    
    if (routeData.route_points && routeData.route_points.length > 0) {
      console.log('\n=== ROUTE WAYPOINTS ===');
      console.log('Start point:', routeData.route_points[0]);
      console.log('End point:', routeData.route_points[routeData.route_points.length - 1]);
      
      // Check if route passes over land (simplified check)
      console.log('\n=== ROUTE ANALYSIS ===');
      const midPoint = routeData.route_points[Math.floor(routeData.route_points.length / 2)];
      console.log('Middle waypoint:', midPoint);
      
      // Flag potential land crossing issues
      if (routeData.route_points.length < 5) {
        console.warn('⚠️  WARNING: Route has very few waypoints - may cross land!');
      }
      
      console.log('Routing details:', routeData.routing_details);
    }
    
  } catch (error) {
    console.error('❌ TEST FAILED:', error.message);
    console.error('Full error:', error);
  }
};

// Run with global fetch (if available) or use node-fetch
if (typeof fetch === 'undefined') {
  // For Node.js environments that don't have fetch
  console.log('Note: This script requires fetch API. Try running in a browser console or install node-fetch.');
  console.log('Or test manually at: http://localhost:3000/weather');
} else {
  test();
}
