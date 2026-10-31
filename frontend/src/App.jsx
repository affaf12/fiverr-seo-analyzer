import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({ title: '', description: '', tags: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      // Vercel par dono same domain par honge isliye '/api/analyze' chalega
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert("Error analyzing gig. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: 'auto' }}>
      <h1>Fiverr SEO Analyzer</h1>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <label>Gig Title:</label>
        <input type="text" name="title" onChange={handleChange} required style={{ padding: '8px' }} />

        <label>Gig Description:</label>
        <textarea name="description" onChange={handleChange} required rows="5" style={{ padding: '8px' }}></textarea>

        <label>Tags (comma separated):</label>
        <input type="text" name="tags" onChange={handleChange} required style={{ padding: '8px' }} />

        <button type="submit" disabled={loading} style={{ padding: '10px', backgroundColor: '#1dbf73', color: 'white', border: 'none', cursor: 'pointer', marginTop: '10px' }}>
          {loading ? 'Analyzing...' : 'Analyze Gig'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
          <h2>Your Score: {result.score} / 100</h2>
          <ul>
            {result.feedback.map((fb, index) => (
              <li key={index}>{fb}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
