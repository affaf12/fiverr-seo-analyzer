import React, { useState } from 'react';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [result, setResult] = useState(null);

  // Form state (Aapke purane Streamlit code ki tarah)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    tags: '',
    primary_keywords: '',
    has_faqs: false,
    has_packages: false,
    has_delivery_info: false,
    has_image: false,
    has_video: false,
    image_contains_text: false,
    seller_level: 'none',
    response_time_hours: 4,
    completion_rate: 95
  });

  // Input change handle karna
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Fiverr URL se data fetch karna
  const handleFetchUrl = async () => {
    if (!url) return alert("Pehle URL dalein!");
    setFetching(true);
    try {
      const response = await fetch('/api/fetch-fiverr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();
      
      if (response.ok) {
        setFormData(prev => ({
          ...prev,
          title: data.title || prev.title,
          description: data.description || prev.description,
          tags: data.tags ? data.tags.join(', ') : prev.tags,
          seller_level: data.seller_level || prev.seller_level,
          has_image: data.has_image || prev.has_image,
          has_video: data.has_video || prev.has_video
        }));
        alert("Data fetch ho gaya!");
      } else {
        alert("Fetch error: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      alert("URL fetch nahi ho saka.");
    }
    setFetching(false);
  };

  // Form submit karke analyze karna
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    // Data ko backend format ke mutabiq tayyar karna
    const payload = {
      title: formData.title,
      description: formData.description,
      tags: formData.tags.split(',').map(t => t.trim()).filter(t => t),
      primary_keywords: formData.primary_keywords.split(',').map(t => t.trim()).filter(t => t),
      extras: {
        has_faqs: formData.has_faqs,
        has_packages: formData.has_packages,
        has_delivery_info: formData.has_delivery_info,
        has_image: formData.has_image,
        has_video: formData.has_video,
        image_contains_text: formData.image_contains_text,
        seller_level: formData.seller_level === 'none' ? null : formData.seller_level,
        response_time_hours: parseInt(formData.response_time_hours),
        completion_rate: parseInt(formData.completion_rate)
      }
    };

    // Agar primary keywords khali hain toh tags use karlo
    if (payload.primary_keywords.length === 0) {
      payload.primary_keywords = payload.tags.slice(0, 2);
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      
      if (response.ok) {
        setResult(data);
      } else {
        alert("Analysis failed. Backend error.");
      }
    } catch (error) {
      alert("Network error. Please try again.");
    }
    setLoading(false);
  };

  // JSON Report Download karne ka function
  const downloadReport = () => {
    const report = { input: formData, analysis: result };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fiverr_seo_report.json';
    a.click();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '900px', margin: 'auto' }}>
      <h1 style={{ color: '#1dbf73' }}>💡 Fiverr Gig SEO Analyzer (Pro)</h1>
      
      {/* URL Fetch Section */}
      <div style={{ padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px', marginBottom: '20px' }}>
        <label><strong>Fiverr Gig URL (Optional)</strong></label>
        <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
          <input 
            type="text" 
            placeholder="https://www.fiverr.com/username/gig-title" 
            value={url} 
            onChange={(e) => setUrl(e.target.value)} 
            style={{ flex: 1, padding: '8px' }} 
          />
          <button type="button" onClick={handleFetchUrl} disabled={fetching} style={{ padding: '8px 15px', backgroundColor: '#333', color: 'white', border: 'none', cursor: 'pointer' }}>
            {fetching ? 'Fetching...' : '🔗 Fetch from Fiverr'}
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
        {/* Main Details */}
        <div>
          <label><strong>Gig Title:</strong></label>
          <input type="text" name="title" value={formData.title} onChange={handleChange} required style={{ width: '100%', padding: '8px', marginTop: '5px' }} />
        </div>

        <div>
          <label><strong>Gig Description:</strong></label>
          <textarea name="description" value={formData.description} onChange={handleChange} required rows="6" style={{ width: '100%', padding: '8px', marginTop: '5px' }}></textarea>
        </div>

        <div style={{ display: 'flex', gap: '15px' }}>
          <div style={{ flex: 1 }}>
            <label><strong>Tags (comma separated):</strong></label>
            <input type="text" name="tags" value={formData.tags} onChange={handleChange} required style={{ width: '100%', padding: '8px', marginTop: '5px' }} />
          </div>
          <div style={{ flex: 1 }}>
            <label><strong>Primary Keywords (comma separated):</strong></label>
            <input type="text" name="primary_keywords" value={formData.primary_keywords} onChange={handleChange} style={{ width: '100%', padding: '8px', marginTop: '5px' }} />
          </div>
        </div>

        {/* Extras & Seller Info */}
        <div style={{ padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, fontSize: '16px' }}>Extras & Seller Info</h3>
          
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginBottom: '15px' }}>
            <label><input type="checkbox" name="has_faqs" checked={formData.has_faqs} onChange={handleChange} /> Has FAQs?</label>
            <label><input type="checkbox" name="has_packages" checked={formData.has_packages} onChange={handleChange} /> Has Packages?</label>
            <label><input type="checkbox" name="has_delivery_info" checked={formData.has_delivery_info} onChange={handleChange} /> Has Delivery Info?</label>
            <label><input type="checkbox" name="has_image" checked={formData.has_image} onChange={handleChange} /> Has Image?</label>
            <label><input type="checkbox" name="has_video" checked={formData.has_video} onChange={handleChange} /> Has Video?</label>
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <div style={{ flex: 1 }}>
              <label>Seller Level:</label>
              <select name="seller_level" value={formData.seller_level} onChange={handleChange} style={{ width: '100%', padding: '8px', marginTop: '5px' }}>
                <option value="none">None</option>
                <option value="level_one">Level 1</option>
                <option value="level_two">Level 2</option>
                <option value="top_rated">Top Rated</option>
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label>Response Time (Hours):</label>
              <input type="number" name="response_time_hours" value={formData.response_time_hours} onChange={handleChange} style={{ width: '100%', padding: '8px', marginTop: '5px' }} />
            </div>
            <div style={{ flex: 1 }}>
              <label>Completion Rate (%):</label>
              <input type="number" name="completion_rate" value={formData.completion_rate} onChange={handleChange} style={{ width: '100%', padding: '8px', marginTop: '5px' }} />
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} style={{ padding: '12px', backgroundColor: '#1dbf73', color: 'white', fontSize: '16px', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '5px' }}>
          {loading ? 'Analyzing...' : '🚀 Analyze Gig'}
        </button>
      </form>

      {/* Results Section */}
      {result && (
        <div style={{ marginTop: '30px', padding: '20px', border: '2px solid #1dbf73', borderRadius: '8px', backgroundColor: '#fff' }}>
          <h2 style={{ marginTop: 0 }}>🎯 Summary</h2>
          <h1 style={{ color: '#1dbf73', fontSize: '48px', margin: '10px 0' }}>{result.overall_score} / 100</h1>
          <p><strong>Health:</strong> {result.health}</p>
          
          <hr style={{ borderColor: '#eee' }} />

          <h3>📊 Component Scores</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
            {Object.entries(result.components).map(([key, val]) => (
              <div key={key} style={{ padding: '10px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', textAlign: 'center' }}>
                <div style={{ fontSize: '12px', color: '#666' }}>{key}</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1dbf73' }}>{val}</div>
              </div>
            ))}
          </div>

          <h3>🔧 Smart Recommendations</h3>
          <ul style={{ backgroundColor: '#fffbeb', padding: '15px 30px', borderRadius: '5px', border: '1px solid #fde68a' }}>
            {result.recommendations.map((rec, index) => (
              <li key={index} style={{ marginBottom: '8px' }}>{rec}</li>
            ))}
          </ul>

          {result.suggested_title && (
            <div>
              <h3>✍️ Suggested Title</h3>
              <code style={{ display: 'block', padding: '10px', backgroundColor: '#f3f4f6', borderRadius: '5px' }}>{result.suggested_title}</code>
            </div>
          )}

          <button onClick={downloadReport} style={{ marginTop: '20px', padding: '10px 15px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
            ⬇️ Download SEO Report (JSON)
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
