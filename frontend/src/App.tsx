import React, { useState, useEffect } from 'react';
import './App.css';
import { fetchSampleChunks } from './services/api';

function App() {
  const [plainText, setPlainText] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadContent = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchSampleChunks();
        setPlainText(data.plain_text || null);
      } catch (error: any) {
        console.error("Error fetching data:", error);
        setError(error.message || 'Failed to fetch data from backend.');
      } finally {
        setLoading(false);
      }
    };
    loadContent();
  }, []);

  return (
    <div className="App">
      <h1>Newsletter Content</h1>
      {loading && <p>Loading content...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {!loading && !error && (
        <div className="content-container">
          <div className="text-section">
            <h2>Extracted Text</h2>
            {plainText ? (
              <pre>{plainText}</pre>
            ) : (
              <p>No text content found.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
