const testRoute = async () => {
  try {
    // Test locations API
    console.log('Testing locations API...');
    const locResponse = await fetch('http://127.0.0.1:8000/api/locations/global?query=rotterdam');
    const locData = await locResponse.json();
    console.log('Rotterdam location:', locData[0]);
    
    const hamburgResponse = await fetch('http://127.0.0.1:8000/api/locations/global?query=hamburg');
    const hamburgData = await hamburgResponse.json();
    console.log('Hamburg location:', hamburgData[0]);
    
    // Test route optimization
    console.log('\\nTesting route optimization...');
    const routeResponse = await fetch('http://127.0.0.1:8000/routes/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin: { lat: locData[0].latitude, lng: locData[0].longitude },
        destination: { lat: hamburgData[0].latitude, lng: hamburgData[0].longitude },
        vessel_type: 'container',
        optimization: 'fuel'
      })
    });
    
    if (!routeResponse.ok) {
      const errorText = await routeResponse.text();
      throw new Error(`HTTP error! status: ${routeResponse.status}, message: ${errorText}`);
    }
    
    const routeData = await routeResponse.json();
    console.log('\\nRoute optimization result:');
    console.log('- Distance:', routeData.distance_nm, 'nautical miles');
    console.log('- Time:', routeData.estimated_time_hours, 'hours');
    console.log('- Fuel:', routeData.fuel_consumption_mt, 'metric tons');
    console.log('- Route points:', routeData.route_points.length);
    console.log('- Route type:', routeData.route_type);
    console.log('- Vessel type:', routeData.vessel_type);
    console.log('- First route point:', routeData.route_points[0]);
    console.log('- Last route point:', routeData.route_points[routeData.route_points.length - 1]);
    
  } catch (error) {
    console.error('Test failed:', error.message);
    if (error.stack) console.error(error.stack);
  }
};

testRoute();
