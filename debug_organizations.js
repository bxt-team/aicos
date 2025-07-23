// Debug script to check organization loading
// To use this script:
// 1. First install axios: npm install axios
// 2. Get your access token from the browser (see instructions below)
// 3. Run: node debug_organizations.js

const axios = require('axios');

async function debugOrganizations() {
  const baseURL = 'http://localhost:8000';
  
  try {
    // First, try to get auth/me endpoint
    console.log('Testing /auth/me endpoint...');
    
    // You'll need to replace this with an actual token from your browser
    const token = 'YOUR_ACCESS_TOKEN_HERE';
    
    if (token === 'YOUR_ACCESS_TOKEN_HERE') {
      console.log('\n⚠️  Please get your access token from the browser:');
      console.log('1. Open the app in your browser');
      console.log('2. Open Developer Tools (F12)');
      console.log('3. Go to Application/Storage → Local Storage');
      console.log('4. Find "accessToken" and copy its value');
      console.log('5. Replace YOUR_ACCESS_TOKEN_HERE in this script with the actual token');
      return;
    }
    
    const response = await axios.get(`${baseURL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    console.log('\n✅ User data received:');
    console.log('User ID:', response.data.id);
    console.log('Email:', response.data.email);
    console.log('Organizations:', response.data.organizations);
    
    if (response.data.organizations) {
      console.log('\n📋 Organization details:');
      response.data.organizations.forEach((membership, index) => {
        const org = membership.organization || membership;
        console.log(`\n${index + 1}. ${org.name}`);
        console.log(`   ID: ${org.id}`);
        console.log(`   Role: ${membership.role || 'N/A'}`);
        console.log(`   Created: ${org.created_at}`);
      });
    }
    
    // Test organization list endpoint
    console.log('\n\nTesting /api/organizations endpoint...');
    const orgResponse = await axios.get(`${baseURL}/api/organizations`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    console.log('\n✅ Organizations endpoint response:');
    console.log('Count:', orgResponse.data.organizations.length);
    console.log('Data:', JSON.stringify(orgResponse.data.organizations, null, 2));
    
  } catch (error) {
    console.error('\n❌ Error:', error.response?.data || error.message);
    if (error.response?.status === 401) {
      console.log('\n⚠️  Token is invalid or expired. Please login again and get a fresh token.');
    }
  }
}

debugOrganizations();