import React, { useState } from 'react';
import './App.css';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [result, setResult] = useState(null);

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

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleFetchUrl = async () => {
    if (!url) return alert("Pehle Fiverr Gig ka URL dalein!");
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
        alert("Data successfully fetch ho gaya!");
      } else {
        alert("Fetch error: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      alert("URL fetch nahi ho saka. Check karein ke URL sahi hai.");
    }
    setFetching(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

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

  const downloadReport = () => {
    const report = { input: formData, analysis: result };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fiverr_seo_report.json';
    a.click();
  };

  // Chart ke liye data tayyar karna
  const chartData = result ? Object.keys(result.components).map(key => ({
    subject: key,
    score: result.components[key],
    fullMark: 30,
  })) : [];

  return (
    <div style={{ padding: '20px', fontFamily: "'Segoe UI', Roboto, Helvetica, Arial, sans-serif", maxWidth: '1000px', margin: 'auto', backgroundColor: '#f8fafc', minHeight: '100vh' }}>
      
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1 style={{ color: '#1dbf73', margin: '0' }}>💡 Fiverr Gig SEO Analyzer</h1>
        <p style={{ color: '#64748b' }}>Apne Gig ko analyze karein aur 0-100 score haasil karein.</p>
      </div>

      {/* URL Fetch Section */}
      <div style={{ padding: '20px', backgroundColor: '#fff', borderRadius: '10px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', marginBottom: '20px' }}>
        <label style={{ fontWeight: 'bold', color: '#334155' }}>Fiverr Gig URL (Optional)</label>
        <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
          <input 
            type="text" 
            placeholder="https://www.fiverr.com/username/gig-title" 
            value={url} 
            onChange={(e) => setUrl(e.target.value)} 
            style={{ flex: 1, padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1', outline: 'none' }} 
          />
          <button type="button" onClick={handleFetchUrl} disabled={fetching} style={{ padding: '10px 20px', backgroundColor: '#0f172a', color: 'white', border: 'none', borderRadius: '5px', cursor: fetching ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}>
            {fetching ? 'Fetching...' : '🔗 Fetch'}
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
        
        <div>
          <label style={{ fontWeight: 'bold', color: '#334155' }}>Gig Title:</label>
          <input type="text" name="title" value={formData.title} onChange={handleChange} required style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
        </div>

        <div>
          <label style={{ fontWeight: 'bold', color: '#334155' }}>Gig Description:</label>
          <textarea name="description" value={formData.description} onChange={handleChange} required rows="6" style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}></textarea>
        </div>

        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px' }}>
            <label style={{ fontWeight: 'bold', color: '#334155' }}>Tags (comma separated):</label>
            <input type="text" name="tags" value={formData.tags} onChange={handleChange} required style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
          </div>
          <div style={{ flex: '1 1 300px' }}>
            <label style={{ fontWeight: 'bold', color: '#334155' }}>Primary Keywords:</label>
            <input type="text" name="primary_keywords" value={formData.primary_keywords} onChange={handleChange} style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
          </div>
        </div>

        <div style={{ padding: '15px', backgroundColor: '#f1f5f9', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, fontSize: '16px', color: '#334155' }}>Extras & Seller Info</h3>
          
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginBottom: '15px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><input type="checkbox" name="has_faqs" checked={formData.has_faqs} onChange={handleChange} /> Has FAQs?</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><input type="checkbox" name="has_packages" checked={formData.has_packages} onChange={handleChange} /> Has Packages?</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><input type="checkbox" name="has_delivery_info" checked={formData.has_delivery_info} onChange={handleChange} /> Has Delivery Info?</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><input type="checkbox" name="has_image" checked={formData.has_image} onChange={handleChange} /> Has Image?</label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><input type="checkbox" name="has_video" checked={formData.has_video} onChange={handleChange} /> Has Video?</label>
          </div>

          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 200px' }}>
              <label>Seller Level:</label>
              <select name="seller_level" value={formData.seller_level} onChange={handleChange} style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1' }}>
                <option value="none">None</option>
                <option value="level_one">Level 1</option>
                <option value="level_two">Level 2</option>
                <option value="top_rated">Top Rated</option>
              </select>
            </div>
            <div style={{ flex: '1 1 200px' }}>
              <label>Response Time (Hours):</label>
              <input type="number" name="response_time_hours" value={formData.response_time_hours} onChange={handleChange} style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
            </div>
            <div style={{ flex: '1 1 200px' }}>
              <label>Completion Rate (%):</label>
              <input type="number" name="completion_rate" value={formData.completion_rate} onChange={handleChange} style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '5px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} style={{ padding: '15px', backgroundColor: '#1dbf73', color: 'white', fontSize: '18px', fontWeight: 'bold', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', borderRadius: '8px', transition: 'background 0.3s' }}>
          {loading ? 'Analyzing...' : '🚀 Analyze Gig Now'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: '40px', animation: 'fadeIn 0.5s' }}>
          {/* Score Card */}
          <div style={{ textAlign: 'center', padding: '30px', backgroundColor: '#fff', borderRadius: '10px', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', borderTop: '5px solid #1dbf73' }}>
            <h2 style={{ color: '#64748b', margin: '0 0 10px 0', fontSize: '18px' }}>Overall SEO Score</h2>
            <div style={{ fontSize: '64px', fontWeight: '900', color: result.overall_score >= 65 ? '#1dbf73' : '#ef4444', lineHeight: '1' }}>
              {result.overall_score}<span style={{ fontSize: '24px', color: '#94a3b8' }}>/100</span>
            </div>
            <p style={{ margin: '10px 0 0 0', fontSize: '18px', fontWeight: 'bold', color: result.health === 'Perfect' ? '#1dbf73' : result.health === 'Good' ? '#eab308' : '#ef4444' }}>
              {result.health}
            </p>
          </div>

          {/* Charts Section */}
          <div style={{ display: 'flex', gap: '20px', marginTop: '20px', flexWrap: 'wrap' }}>
            
            {/* Radar Chart */}
            <div style={{ flex: '1 1 400px', backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
              <h3 style={{ marginTop: 0, color: '#334155' }}>📊 Radar Chart</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 30]} />
                    <Radar name="Score" dataKey="score" stroke="#1dbf73" fill="#1dbf73" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Bar Chart */}
            <div style={{ flex: '1 1 400px', backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
              <h3 style={{ marginTop: 0, color: '#334155' }}>📈 Component Scores</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" domain={[0, 30]} />
                    <YAxis dataKey="subject" type="category" width={100} tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="score" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', marginTop: '20px' }}>
            <h3 style={{ marginTop: 0, color: '#334155' }}>🔧 Smart Recommendations</h3>
            <ul style={{ paddingLeft: '20px', lineHeight: '1.6', color: '#475569' }}>
              {result.recommendations.map((rec, index) => (
                <li key={index} style={{ marginBottom: '10px' }}>{rec}</li>
              ))}
            </ul>

            {result.suggested_title && (
              <div style={{ marginTop: '20px' }}>
                <h4 style={{ color: '#334155', marginBottom: '5px' }}>✍️ Suggested Title</h4>
                <div style={{ padding: '15px', backgroundColor: '#f8fafc', borderLeft: '4px solid #1dbf73', borderRadius: '4px', fontFamily: 'monospace', color: '#0f172a' }}>
                  {result.suggested_title}
                </div>
              </div>
            )}

            <button onClick={downloadReport} style={{ marginTop: '20px', padding: '12px 20px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }}>
              ⬇️ Download Detailed Report (JSON)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
